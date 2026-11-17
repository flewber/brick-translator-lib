"""BrickLink ids as Brickognize answers them, against a small data extract.

`data/bricklink_ids.json` holds only the entries for the ids seen in
recorded Brickognize replies (parts and colors). The full data file is
not needed.

The extract is Rebrickable data and is not committed (see the README on
Rebrickable's terms), so these tests are skipped where it is absent, as
on CI. To run them, place the extract (or the full data file) at that
path.
"""

from pathlib import Path

import pytest

from brick_translator import Translator

DATA = Path(__file__).parent / "data" / "bricklink_ids.json"

pytestmark = pytest.mark.skipif(
    not DATA.exists(), reason=f"data extract not present: {DATA}"
)

# BrickLink part id -> Rebrickable ids, as the full data file gives them
PART_RESULTS = {
    "3001": ["3001", "3556"],  # one-to-many
    "3010": ["3010", "3010a"],  # one-to-many
    "3001c01": ["30160"],
    "bhol04": ["3001c"],
    "3001old": ["3001a"],
    "3023pb02": ["3023pr0001"],
    "3023pb15R": ["3023pr0014"],  # upper case letter kept as is
    "2456": ["2456"],
    "3024": ["3024"],
}
# Seen in the replies, absent from the data
UNMAPPED_PARTS = ["3001special", "3001oldpb07", "3023old2", "27glass", "29glass"]

COLOR_RESULTS = {
    "5": ["4"], "11": ["0"], "86": ["71"], "85": ["72"], "1": ["15"], "12": ["47"],
}


@pytest.fixture(scope="module")
def translator():
    return Translator.load(DATA)


@pytest.mark.parametrize("bl_id, expected", PART_RESULTS.items())
def test_part_results(translator, bl_id, expected):
    assert translator.translate_part(bl_id, "BrickLink", "Rebrickable") == expected


@pytest.mark.parametrize("bl_id", UNMAPPED_PARTS)
def test_unmapped_part_is_empty_and_unknown(translator, bl_id):
    assert translator.translate_part(bl_id, "BrickLink", "Rebrickable") == []
    assert not translator.knows_part(bl_id, "BrickLink")


@pytest.mark.parametrize("bl_id, expected", COLOR_RESULTS.items())
def test_color_results(translator, bl_id, expected):
    assert translator.translate_color(bl_id, "BrickLink", "Rebrickable") == expected


def test_part_ids_are_case_sensitive(translator):
    assert translator.translate_part("3023PB15r", "BrickLink", "Rebrickable") == []


def test_all_recorded_colors_map_to_exactly_one(translator):
    for bl_id in ["1", "2", "3", "5", "6", "7", "9", "10", "11", "12", "17", "27",
                  "49", "66", "85", "86", "99", "105", "157"]:
        assert len(translator.translate_color(bl_id, "BrickLink", "Rebrickable")) == 1, bl_id
