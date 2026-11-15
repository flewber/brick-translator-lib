# brick-translator-lib

Translate brick part numbers and color IDs between naming schemes:
Rebrickable, BrickLink, BrickOwl, Brickset, LDraw and LEGO for parts;
Rebrickable, BrickLink, BrickOwl, LDraw, LEGO and Peeron for colors.

The mapping data comes from the [Rebrickable](https://rebrickable.com/)
API and is not part of this repo. You build the data file yourself with
your own API key (below).

## Use

```python
from brick_translator import Translator

translator = Translator.load("part_translations.json")

translator.translate_part("3001", "BrickLink", "BrickOwl")   # ['771344']
translator.translate_part("3001", "Rebrickable", "LEGO")     # ['15589', '3001', ...]
translator.part_ids("3001")          # every known ID of a Rebrickable part, by scheme
translator.knows_part("3001", "BrickLink")                   # True
translator.translate_color(0, "Rebrickable", "BrickLink")    # ['11']
translator.info                      # date, source and completeness of the data
```

- A translation returns a list, because one part in one scheme can be
  several parts in another. The list is empty when the part is unknown
  or has no ID in the target scheme; `knows_part` tells the two apart.
- Rebrickable is the hub. A translation between two other schemes goes
  through every Rebrickable part that lists the given ID.
- Scheme names are not case sensitive. An unknown scheme raises
  `UnknownSchemeError`.
- A missing or damaged data file raises `TranslationDataError`. It is
  never reported as "no translation found".
- `Translator.load()` without a path reads the file named in the
  environment variable `BRICK_TRANSLATOR_DATA`, or
  `part_translations.json` in the working directory.
- IDs are strings, also for colors.

## Building the data file

1. Download and extract `parts.csv` from
   https://rebrickable.com/downloads/.
2. Get an API key: on Rebrickable, Account, Settings, API.
3. Give the key to the builder, either in the environment variable
   `REBRICKABLE_API_KEY`, or by copying `keys_example.py` to `keys.py`
   and pasting the key there (`keys.py` is ignored by git).
4. `pip install rebrick`
5. `python -m brick_translator.build --parts-csv parts.csv`

The build asks for 100 parts per request, about one request per second,
so it takes a while. It saves after every request and resumes where it
stopped. It refuses to resume with a different `parts.csv` than it
started with; use `--restart` for that.

The data file records its format number, the date it was started and
last written, the SHA-256 of the `parts.csv` it was built from, whether
the build finished (`complete`), and the parts the API did not return
(`not_returned`). Loading a file that is not complete gives a warning,
or an error with `Translator.load(path, require_complete=True)`.

The file holds Rebrickable's data. Read Rebrickable's terms before you
pass it on.

### Not tested against the live API

The tests run the builder against made-up API replies. The two functions
that talk to the network (`_rebrick_fetchers` in `build.py`) have not
been run in this version. The shape of a color record is taken from a
description of the API, not from a recorded reply.

## Old interface

`translate_lib.py` keeps the original function names (`tranlate_from_to`
and the others, spelled as they were) so old scripts keep running. They
give a deprecation warning. The differences are listed at the top of
that file.

Data files in the original flat format still load. They carry no date,
no Brickset IDs and no colors, so rebuild when you can.

## Development

```
uv run pytest
```
