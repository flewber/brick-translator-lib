"""Build the translation data file from the Rebrickable API.

    python -m brick_translator.build --parts-csv parts.csv

Needs `parts.csv` from https://rebrickable.com/downloads/ (the list of
part numbers to ask for), a Rebrickable API key, and the `rebrick`
package (`pip install brick-translator[fetch]`).

The build takes a while (one request per 100 parts, about one per
second). It saves as it goes and resumes where it stopped.

The generated file contains Rebrickable's data. Check Rebrickable's
terms before passing it on to anyone.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, Iterable

from .translator import COLOR_SCHEMES, DEFAULT_DATA_FILE, FORMAT, PART_SCHEMES, REBRICKABLE

SOURCE = "Rebrickable API v3 (external_ids of lego/parts and lego/colors)"
BATCH = 100
MIN_SECONDS_BETWEEN_REQUESTS = 1.1

PartFetch = Callable[[list[str]], list[dict]]
ColorFetch = Callable[[], list[dict]]


class BuildError(Exception):
    pass


def read_part_numbers(parts_csv: str | os.PathLike) -> tuple[list[str], str]:
    """Part numbers from Rebrickable's parts.csv, and the file's SHA-256."""
    data = Path(parts_csv).read_bytes()
    rows = csv.reader(data.decode("utf-8-sig").splitlines())
    header = next(rows, None)
    if not header or "part_num" not in header:
        raise BuildError(f"{parts_csv}: no 'part_num' column; is this Rebrickable's parts.csv?")
    col = header.index("part_num")
    numbers = [row[col] for row in rows if row]
    return numbers, hashlib.sha256(data).hexdigest()


def part_entry(result: dict) -> dict[str, list[str]]:
    """The external IDs of one API part record, by scheme, as strings."""
    external = result.get("external_ids") or {}
    entry: dict[str, list[str]] = {}
    for scheme in PART_SCHEMES:
        if scheme == REBRICKABLE:
            continue
        ids = external.get(scheme)
        if ids:
            entry[scheme] = list(dict.fromkeys(str(i) for i in ids))
    return entry


def color_entry(result: dict) -> dict:
    """The external IDs of one API color record.

    The API gives, per scheme, an object with `ext_ids` (and names in
    `ext_descrs`). A plain list of IDs is accepted too.
    """
    external = result.get("external_ids") or {}
    entry: dict = {"name": str(result.get("name", ""))}
    for scheme in COLOR_SCHEMES:
        if scheme == REBRICKABLE:
            continue
        value = external.get(scheme)
        ids = value.get("ext_ids") if isinstance(value, dict) else value
        if ids:
            entry[scheme] = list(dict.fromkeys(str(i) for i in ids if i is not None))
    return entry


def new_state(parts_csv_sha256: str, part_total: int) -> dict:
    return {
        "format": FORMAT,
        "source": SOURCE,
        "started": datetime.date.today().isoformat(),
        "updated": datetime.date.today().isoformat(),
        "complete": False,
        "parts_csv_sha256": parts_csv_sha256,
        "parts_csv_rows": part_total,
        "next_row": 0,
        "not_returned": [],
        "parts": {},
        "colors": {},
    }


def load_state(path: Path, parts_csv_sha256: str, part_total: int) -> dict:
    """A saved build to resume, or a fresh one if there is no file."""
    if not path.exists():
        return new_state(parts_csv_sha256, part_total)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise BuildError(f"{path} exists but cannot be read ({e}). Move it away or use --restart.") from e
    if not isinstance(state, dict) or state.get("format") != FORMAT:
        raise BuildError(f"{path} is not in data format {FORMAT}. Move it away or use --restart.")
    if state.get("parts_csv_sha256") != parts_csv_sha256:
        raise BuildError(
            f"{path} was built from a different parts.csv. A resumed build would mix two "
            "catalog versions. Use --restart to build from the start."
        )
    return state


def save_state(path: Path, state: dict) -> None:
    """Write the file whole or not at all."""
    state["updated"] = datetime.date.today().isoformat()
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, path)


def build(
    part_numbers: list[str],
    state: dict,
    fetch_parts: PartFetch,
    fetch_colors: ColorFetch | None = None,
    *,
    save: Callable[[dict], None] = lambda state: None,
    batch: int = BATCH,
    progress: Callable[[int, int], None] = lambda done, total: None,
) -> dict:
    """Fill `state` from the API, starting at `state["next_row"]`.

    `fetch_parts(numbers)` returns the API's part records for those
    numbers. Parts asked for and not returned are listed in
    `state["not_returned"]`, never dropped silently. `save` is called
    after every batch.
    """
    total = len(part_numbers)
    row = state["next_row"]
    if not 0 <= row <= total:
        raise BuildError(f"saved position {row} is outside the part list (0 to {total})")
    while row < total:
        numbers = part_numbers[row : row + batch]
        wanted = set(numbers)
        for result in fetch_parts(numbers):
            number = str(result.get("part_num"))
            if number not in wanted:
                raise BuildError(f"the API returned part {number!r}, which was not asked for")
            wanted.discard(number)
            state["parts"][number] = part_entry(result)
        state["not_returned"].extend(n for n in numbers if n in wanted and n not in state["parts"])
        row += len(numbers)
        state["next_row"] = row
        save(state)
        progress(row, total)
    if fetch_colors is not None:
        state["colors"] = {str(c["id"]): color_entry(c) for c in fetch_colors()}
    state["complete"] = True
    save(state)
    return state


# The network side. Not covered by the tests: it needs an API key.


def _api_key() -> str:
    key = os.environ.get("REBRICKABLE_API_KEY")
    if not key:
        sys.path.insert(0, os.getcwd())
        try:
            import keys  # type: ignore[import-not-found]

            key = keys.YOUR_REBRICKABLE_API_KEY
        except ImportError:
            pass
    if not key or key == "PASTE_YOUR_KEY_HERE":
        raise BuildError("no API key: set REBRICKABLE_API_KEY, or create keys.py from keys_example.py")
    return key


def _rebrick_fetchers(key: str) -> tuple[PartFetch, ColorFetch]:
    try:
        import rebrick  # type: ignore[import-not-found]
    except ImportError:
        raise BuildError("the `rebrick` package is needed to fetch: pip install rebrick") from None
    rebrick.init(key)
    last = [0.0]

    def paced(call, **kwargs) -> dict:
        wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.monotonic() - last[0])
        if wait > 0:
            time.sleep(wait)
        last[0] = time.monotonic()
        return json.loads(call(**kwargs).read())

    def fetch_parts(numbers: list[str]) -> list[dict]:
        reply = paced(rebrick.lego.get_parts, part_ids=numbers)
        if reply.get("next"):
            raise BuildError("the API split one batch over several pages; use a smaller --batch")
        return reply["results"]

    def fetch_colors() -> list[dict]:
        colors: list[dict] = []
        page = 1
        while True:
            reply = paced(rebrick.lego.get_colors, page=page)
            colors.extend(reply["results"])
            if not reply.get("next"):
                return colors
            page += 1

    return fetch_parts, fetch_colors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the part and color translation data file.")
    parser.add_argument("--parts-csv", default="parts.csv", help="Rebrickable's parts.csv")
    parser.add_argument("--out", default=DEFAULT_DATA_FILE)
    parser.add_argument("--batch", type=int, default=BATCH)
    parser.add_argument("--restart", action="store_true", help="discard a saved build and start over")
    parser.add_argument("--no-colors", action="store_true")
    args = parser.parse_args(argv)
    out = Path(args.out)
    try:
        numbers, digest = read_part_numbers(args.parts_csv)
        state = new_state(digest, len(numbers)) if args.restart else load_state(out, digest, len(numbers))
        if state["complete"]:
            print(f"{out} is already complete ({len(state['parts'])} parts). Use --restart to rebuild.")
            return 0
        if state["next_row"]:
            print(f"resuming at part {state['next_row']} of {len(numbers)}")
        fetch_parts, fetch_colors = _rebrick_fetchers(_api_key())
        build(
            numbers,
            state,
            fetch_parts,
            None if args.no_colors else fetch_colors,
            save=lambda s: save_state(out, s),
            batch=args.batch,
            progress=lambda done, total: print(f"{done}/{total} parts"),
        )
    except (BuildError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(
        f"done: {len(state['parts'])} parts, {len(state['colors'])} colors, "
        f"{len(state['not_returned'])} parts not returned by the API"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
