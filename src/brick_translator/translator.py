"""Translate part and color IDs between naming schemes.

Rebrickable is the hub: the data file holds, for each Rebrickable part
(or color), the IDs other sites use for it. A translation from scheme A
to scheme B goes through every Rebrickable entry that lists the A ID.
"""

from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from pathlib import Path

REBRICKABLE = "Rebrickable"
PART_SCHEMES = (REBRICKABLE, "BrickLink", "BrickOwl", "Brickset", "LDraw", "LEGO")
COLOR_SCHEMES = (REBRICKABLE, "BrickLink", "BrickOwl", "LDraw", "LEGO", "Peeron")

FORMAT = 2
DEFAULT_DATA_FILE = "part_translations.json"
DATA_FILE_ENV = "BRICK_TRANSLATOR_DATA"

# The first data format: one flat dictionary of prefixed IDs.
LEGACY_PREFIXES = {
    "RB_": REBRICKABLE,
    "BL_": "BrickLink",
    "BO_": "BrickOwl",
    "BS_": "Brickset",
    "LG_": "LEGO",
}
LEGACY_COUNTER_KEY = "running_part_count"


class TranslationDataError(Exception):
    """The data file is missing, unreadable or not in a known format."""


class UnknownSchemeError(ValueError):
    """A naming scheme name that this library does not know."""


@dataclass(frozen=True)
class DataInfo:
    """Where the loaded data came from and how far it can be trusted."""

    format: int | str
    source: str | None
    updated: str | None  # ISO date of the last write by the builder
    complete: bool  # False: the builder was interrupted, parts are missing
    part_count: int
    color_count: int
    notes: tuple[str, ...] = ()


def _canonical(scheme: str, known: tuple[str, ...]) -> str:
    if isinstance(scheme, str):
        for name in known:
            if name.lower() == scheme.lower():
                return name
    raise UnknownSchemeError(f"unknown naming scheme {scheme!r}; known: {', '.join(known)}")


class _Index:
    """IDs of one kind (parts or colors), keyed by Rebrickable ID."""

    def __init__(self, entries: dict[str, dict[str, list[str]]], schemes: tuple[str, ...]):
        self.schemes = schemes
        self.entries = entries
        # (scheme, external id) -> Rebrickable IDs, in file order
        self.reverse: dict[tuple[str, str], list[str]] = {}
        for rb_id, by_scheme in entries.items():
            for scheme, ids in by_scheme.items():
                for ext_id in ids:
                    owners = self.reverse.setdefault((scheme, ext_id), [])
                    if rb_id not in owners:
                        owners.append(rb_id)

    def to_rebrickable(self, item_id, scheme: str) -> list[str]:
        scheme = _canonical(scheme, self.schemes)
        item_id = str(item_id)
        if scheme == REBRICKABLE:
            return [item_id] if item_id in self.entries else []
        return list(self.reverse.get((scheme, item_id), ()))

    def knows(self, item_id, scheme: str) -> bool:
        return bool(self.to_rebrickable(item_id, scheme))

    def translate(self, item_id, from_scheme: str, to_scheme: str) -> list[str]:
        from_scheme = _canonical(from_scheme, self.schemes)
        to_scheme = _canonical(to_scheme, self.schemes)
        rb_ids = self.to_rebrickable(item_id, from_scheme)
        if from_scheme == to_scheme:
            return [str(item_id)] if rb_ids else []
        if to_scheme == REBRICKABLE:
            return rb_ids
        out: list[str] = []
        for rb_id in rb_ids:
            for ext_id in self.entries[rb_id].get(to_scheme, ()):
                if ext_id not in out:
                    out.append(ext_id)
        return out

    def all_ids(self, rb_id) -> dict[str, list[str]]:
        entry = self.entries.get(str(rb_id))
        if entry is None:
            return {}
        return {scheme: list(ids) for scheme, ids in entry.items() if ids}


def _check_entries(raw, what: str, schemes: tuple[str, ...]) -> dict[str, dict[str, list[str]]]:
    if not isinstance(raw, dict):
        raise TranslationDataError(f"'{what}' must be an object keyed by Rebrickable ID")
    out: dict[str, dict[str, list[str]]] = {}
    for rb_id, by_scheme in raw.items():
        if not isinstance(by_scheme, dict):
            raise TranslationDataError(f"{what} {rb_id!r}: expected an object of scheme to IDs")
        clean: dict[str, list[str]] = {}
        for scheme, ids in by_scheme.items():
            if scheme == "name":  # colors carry their Rebrickable name
                continue
            if scheme not in schemes or scheme == REBRICKABLE:
                raise TranslationDataError(f"{what} {rb_id!r}: unexpected scheme {scheme!r}")
            if not isinstance(ids, list):
                raise TranslationDataError(f"{what} {rb_id!r}: IDs for {scheme} must be a list")
            clean[scheme] = [str(i) for i in ids]
        out[str(rb_id)] = clean
    return out


def _from_legacy(raw: dict) -> dict[str, dict[str, list[str]]]:
    """Rebuild per-part entries from the first, flat format.

    Only the "RB_" keys are used. In that format a non-Rebrickable ID
    shared by several Rebrickable parts kept only the last one, so the
    other keys are not reliable; the "RB_" rows are.
    """
    parts: dict[str, dict[str, list[str]]] = {}
    for key, others in raw.items():
        if not key.startswith("RB_"):
            continue
        if not isinstance(others, list):
            raise TranslationDataError(f"legacy entry {key!r} is not a list")
        entry: dict[str, list[str]] = {}
        for other in others:
            scheme = LEGACY_PREFIXES.get(str(other)[:3])
            if scheme is None or scheme == REBRICKABLE:
                continue
            ids = entry.setdefault(scheme, [])
            if other[3:] not in ids:
                ids.append(other[3:])
        parts[key[3:]] = entry
    return parts


class Translator:
    """Loaded translation data. Build one with `Translator.load(path)`."""

    def __init__(self, parts: dict, colors: dict | None = None, info: DataInfo | None = None):
        self._parts = _Index(_check_entries(parts, "parts", PART_SCHEMES), PART_SCHEMES)
        self._colors = _Index(_check_entries(colors or {}, "colors", COLOR_SCHEMES), COLOR_SCHEMES)
        self.info = info or DataInfo(
            FORMAT, None, None, True, len(self._parts.entries), len(self._colors.entries)
        )

    @classmethod
    def load(cls, path: str | os.PathLike | None = None, *, require_complete: bool = False):
        """Read a data file written by `brick_translator.build`.

        `path` defaults to the environment variable BRICK_TRANSLATOR_DATA,
        then to `part_translations.json` in the working directory. A
        missing or damaged file raises TranslationDataError; it is never
        treated as "no translation found".
        """
        path = Path(path or os.environ.get(DATA_FILE_ENV) or DEFAULT_DATA_FILE)
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            raise TranslationDataError(
                f"translation data file not found: {path}. "
                "Create it with `python -m brick_translator.build` (see README)."
            ) from None
        except (OSError, json.JSONDecodeError) as e:
            raise TranslationDataError(f"cannot read translation data file {path}: {e}") from e
        if not isinstance(raw, dict):
            raise TranslationDataError(f"{path}: top level must be an object")

        if "format" not in raw:
            if LEGACY_COUNTER_KEY not in raw:
                raise TranslationDataError(f"{path}: no 'format' field and not the legacy format")
            parts, colors = _from_legacy(raw), {}
            notes = (
                "legacy format: no date recorded, no Brickset or LDraw IDs, no colors; "
                "cannot tell whether the build finished",
            )
            meta = {"format": "legacy", "complete": False}
        elif raw["format"] == FORMAT:
            parts, colors, meta, notes = raw.get("parts"), raw.get("colors") or {}, raw, ()
            if parts is None:
                raise TranslationDataError(f"{path}: no 'parts' field")
        else:
            raise TranslationDataError(
                f"{path}: data format {raw['format']!r} is not supported (this library reads {FORMAT})"
            )

        complete = bool(meta.get("complete", False))
        translator = cls(parts, colors)
        translator.info = DataInfo(
            format=meta["format"],
            source=meta.get("source"),
            updated=meta.get("updated"),
            complete=complete,
            part_count=len(translator._parts.entries),
            color_count=len(translator._colors.entries),
            notes=notes,
        )
        if not complete:
            if require_complete:
                raise TranslationDataError(f"{path}: the data file is not marked complete")
            warnings.warn(
                f"{path}: translation data is not marked complete; some parts may be missing",
                stacklevel=2,
            )
        return translator

    # Parts

    def translate_part(self, part_id, from_scheme: str, to_scheme: str) -> list[str]:
        """IDs in `to_scheme` for the part called `part_id` in `from_scheme`.

        Returns an empty list when the part is unknown or has no ID in
        the target scheme; `knows_part` tells the two apart. Scheme names
        are not case sensitive. An unknown scheme raises UnknownSchemeError.
        """
        return self._parts.translate(part_id, from_scheme, to_scheme)

    def knows_part(self, part_id, scheme: str = REBRICKABLE) -> bool:
        return self._parts.knows(part_id, scheme)

    def part_ids(self, rebrickable_part_id) -> dict[str, list[str]]:
        """Every known ID of one Rebrickable part, by scheme. Empty if unknown."""
        return self._parts.all_ids(rebrickable_part_id)

    # Colors

    def translate_color(self, color_id, from_scheme: str, to_scheme: str) -> list[str]:
        """Like translate_part, for color IDs. IDs are returned as strings."""
        return self._colors.translate(color_id, from_scheme, to_scheme)

    def knows_color(self, color_id, scheme: str = REBRICKABLE) -> bool:
        return self._colors.knows(color_id, scheme)

    def color_ids(self, rebrickable_color_id) -> dict[str, list[str]]:
        return self._colors.all_ids(rebrickable_color_id)


_default: Translator | None = None


def default_translator() -> Translator:
    """The translator for the default data file, loaded on first use."""
    global _default
    if _default is None:
        _default = Translator.load()
    return _default


def translate_from_to(part_id, from_scheme: str, to_scheme: str) -> list[str]:
    """`Translator.translate_part` on the default data file."""
    return default_translator().translate_part(part_id, from_scheme, to_scheme)
