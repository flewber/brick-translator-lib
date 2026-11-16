# BrickLink ids to Rebrickable ids

Question: is `translate_part(id, "BrickLink", "Rebrickable")` and
`translate_color(...)` enough to use Brickognize answers, which come in
BrickLink part and color ids? Short answer: yes for colors, mostly yes
for parts, with one-to-many and unmapped ids that the caller must handle.
No new library code was needed; this note and `tests/test_bricklink_ids.py`
record the evidence.

Numbers come from the full data file built on 2026-11-16 (65,034 parts,
275 colors, `complete: true`, one part not returned by the API) and from
four recorded Brickognize replies (all with parts, three with colors).
The full file is Rebrickable data and is not in this repo; the tests use
`tests/data/bricklink_ids.json`, a 37-entry extract.

## 1. Recorded replies

21 distinct part ids, 19 distinct color ids.

Colors: all 19 map to exactly one Rebrickable color, and the names match
(for example BrickLink 5 Red to 4, 11 Black to 0, 86 Light Bluish Gray to
71, 85 Dark Bluish Gray to 72, 1 White to 15, 12 Trans-Clear to 47).

Parts: 14 map to one Rebrickable part, 2 to two parts, 5 to none.
- Two parts: `3001` gives `3001` and `3556`; `3010` gives `3010` and `3010a`.
- One part: `3001c01` gives `30160`, `bhol04` gives `3001c`, `3001old`
  gives `3001a`, `3023pb02` gives `3023pr0001`, `3023pb12` gives
  `3023pr0011`, `3023pb15R` gives `3023pr0014`, `3023old` gives `3023a`,
  and `2456`, `3023`, `3623`, `3024`, `7896`, `29541`, `48201` give
  themselves.
- None: `3001special`, `3001oldpb07`, `3023old2`, `27glass`, `29glass`
  (no entry with that BrickLink id; `knows_part` is False). Parts 27 and 29 themselves exist
  (guess: the `glass` ids are variants Rebrickable does not list).

So not every part id gives exactly one result. Of the 21 part ids, 2 are
one-to-many and 5 are unmapped.

## 2. Whole data file

Parts:
- 61,472 distinct BrickLink part ids. 60,845 map to one Rebrickable part,
  627 to more than one (580 to two, up to 64 for one id).
- 3,343 of 65,034 Rebrickable parts have no BrickLink id (488 of them
  have an id in some other scheme). 337 of these have a short numeric id,
  for example `10057`, `11251`, `1124`.
- 543 Rebrickable parts list more than one BrickLink id (for example
  `003402`: `310.3stk01`, `311.1stk01`, `312.3stk01`).
- One-to-many examples: `3001` to `3001`, `3556`; `26697` to `100097`,
  `26697`; `2599a` to `10190`, `59275`; `60616` to `60616a`, `60616b`;
  `10305pb01` to `10305pr0001`, `10305pr0002`.

Colors:
- 214 distinct BrickLink color ids. 212 map to one Rebrickable color, 2
  to two: `77` to `148`, `1103`; `72` to `313`, `1051`.
- 59 of 275 Rebrickable colors have no BrickLink id (for example `-1`
  [Unknown], `32` Trans-Black IR Lens, `1005` Trans-Fire Yellow, `1008`
  Vintage Blue, Duplo and Fabuland colors). No color lists more than one
  BrickLink id.

## 3. Id forms

Shown from the data:
- **Case matters and is kept.** 3,483 BrickLink part ids contain an upper
  case letter (`3023pb15R`, `Mx1041Apb02`, `FTGpb065c01`). No two ids
  differ only by case, so a case-insensitive fallback could not be
  ambiguous in this data. Lookup is exact today: `3023PB15r` finds
  nothing (tested).
- **Suffixes are separate ids, not noise.** `3010` and `3010a` are both
  BrickLink `3010`; `3001old` is a different part from `3001`. Of 705
  ids of the form digits plus one letter, only 366 also exist without the
  letter, so stripping a suffix would often hit a different part or
  nothing. Do not strip.
- **Printed and assembly ids** (`pb`, `c01`) are present, 38,192 and
  13,226 ids, and map to Rebrickable `pr` and `c` ids (`3023pb02` to
  `3023pr0001`). Brickognize ids of this kind that the data lacks (the
  five unmapped above) exist; I cannot tell from the data whether
  they are newer than the file or never listed by Rebrickable.
- **Leading zeros:** only 31 ids start with a zero (`0904`,
  `03093card08`), all real BrickLink ids, so do not strip or add them.
- A BrickLink id can equal a *different* Rebrickable id: 143 cases, such
  as BrickLink `970c55`, which is Rebrickable `970c24`. Do not assume a
  BrickLink id is also a Rebrickable id; always translate.
- Suffixes such as `special` occur nowhere in the data, and `glass` once
  (`7026glass`). Guess: Brickognize lists catalog entries that Rebrickable
  does not carry.

## 4. What a caller should do

Options for a one-to-many or unmapped id:
1. Take the first candidate. Simple, but file order is not a ranking, and
   it hides the problem. Not recommended.
2. Prefer the candidate whose id equals the BrickLink id. It decides
   only 163 of the 627 one-to-many ids (`3001` gives `3001`, `3010` gives
   `3010`) and fails for most printed parts, so it is a partial
   heuristic.
3. Keep all candidates and let the caller decide with its own context.
   Honest, and cheap: in the sorter the next step is a bin or category
   lookup, and near-duplicates (`3001` and `3556`) are usually the same
   physical brick in the same bin.
4. Treat an unmapped id as "unknown part": route to the reject or
   unidentified bin, and keep the BrickLink id for the log. Do not guess
   by suffix stripping or fuzzy matching.

Recommendation: use the list as given (option 3, which is what
`translate_part` already returns), check `knows_part(id, "BrickLink")`
to tell unmapped from known, and send unmapped ids to the unknown route
(option 4). If one id is needed, use option 2 as a tie-break only when
exactly one candidate equals the BrickLink id, and log everything else
as ambiguous.

A small helper returning candidates plus a reason ("exact", "several",
"unmapped") is possible, but the policy (what counts as sure, whether to
tie-break) is a decision for the project, so it is not built here.
