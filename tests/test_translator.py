import json
import warnings

import pytest

from brick_translator import TranslationDataError, Translator, UnknownSchemeError
from brick_translator import translator as translator_module

PARTS = {
    "3001": {
        "BrickLink": ["3001"],
        "BrickOwl": ["771344"],
        "Brickset": ["15589", "3001"],
        "LDraw": ["3001"],
        "LEGO": ["15589", "3001"],
    },
    # A second Rebrickable part that shares LEGO ID 3001 with the first
    "3001a": {"BrickLink": ["3001old"], "LEGO": ["3001"]},
    "upn0001": {},
}
COLORS = {
    "0": {"name": "Black", "BrickLink": ["11"], "LEGO": ["26", "149"]},
    "4": {"name": "Red", "BrickLink": ["5"]},
}


def write(tmp_path, content, name="data.json"):
    path = tmp_path / name
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return path


def v2(**extra):
    return {"format": 2, "source": "test", "updated": "2026-01-02", "complete": True,
            "parts": PARTS, "colors": COLORS, **extra}


@pytest.fixture
def translator(tmp_path):
    return Translator.load(write(tmp_path, v2()))


def test_rebrickable_to_other(translator):
    assert translator.translate_part("3001", "Rebrickable", "BrickOwl") == ["771344"]
    assert translator.translate_part("3001", "Rebrickable", "LEGO") == ["15589", "3001"]


def test_other_to_rebrickable(translator):
    assert translator.translate_part("771344", "BrickOwl", "Rebrickable") == ["3001"]


def test_between_two_other_schemes(translator):
    assert translator.translate_part("3001", "BrickLink", "BrickOwl") == ["771344"]


def test_id_shared_by_two_rebrickable_parts_keeps_both(translator):
    # The first data format kept only the last owner of a shared ID.
    assert translator.translate_part("3001", "LEGO", "Rebrickable") == ["3001", "3001a"]
    assert translator.translate_part("3001", "LEGO", "BrickLink") == ["3001", "3001old"]


def test_same_scheme_in_and_out(translator):
    # The original returned "invalid site name" here.
    assert translator.translate_part("3001", "BrickLink", "BrickLink") == ["3001"]
    assert translator.translate_part("3001", "Rebrickable", "Rebrickable") == ["3001"]
    assert translator.translate_part("nope", "BrickLink", "BrickLink") == []


def test_brickset_ids_are_found(translator):
    assert translator.translate_part("15589", "Brickset", "Rebrickable") == ["3001"]
    assert translator.translate_part("15589", "BrickSet", "Rebrickable") == ["3001"]  # old spelling


def test_unknown_part_is_empty_and_distinguishable(translator):
    assert translator.translate_part("nope", "Rebrickable", "BrickLink") == []
    assert not translator.knows_part("nope")
    # known part with no ID in the target scheme
    assert translator.translate_part("upn0001", "Rebrickable", "BrickLink") == []
    assert translator.knows_part("upn0001")
    assert translator.knows_part("3001old", "BrickLink")


def test_unknown_scheme_raises(translator):
    with pytest.raises(UnknownSchemeError):
        translator.translate_part("3001", "Rebrickable", "Bricklunk")
    with pytest.raises(UnknownSchemeError):
        translator.translate_part("3001", "Nowhere", "BrickLink")
    with pytest.raises(ValueError):
        translator.knows_part("3001", None)


def test_part_ids(translator):
    assert translator.part_ids("3001a") == {"BrickLink": ["3001old"], "LEGO": ["3001"]}
    assert translator.part_ids("nope") == {}


def test_numeric_input_is_accepted(translator):
    assert translator.translate_part(3001, "BrickLink", "BrickOwl") == ["771344"]


def test_colors(translator):
    assert translator.translate_color(0, "Rebrickable", "BrickLink") == ["11"]
    assert translator.translate_color("11", "BrickLink", "LEGO") == ["26", "149"]
    assert translator.translate_color(5, "BrickLink", "Rebrickable") == ["4"]
    assert translator.translate_color(999, "Rebrickable", "BrickLink") == []
    assert translator.knows_color(4) and not translator.knows_color(999)
    assert translator.color_ids(0) == {"BrickLink": ["11"], "LEGO": ["26", "149"]}
    with pytest.raises(UnknownSchemeError):
        translator.translate_color(0, "Rebrickable", "Brickset")  # not a color scheme


def test_info(translator):
    info = translator.info
    assert (info.format, info.updated, info.complete) == (2, "2026-01-02", True)
    assert (info.part_count, info.color_count) == (3, 2)


def test_missing_file_raises(tmp_path):
    with pytest.raises(TranslationDataError, match="not found"):
        Translator.load(tmp_path / "absent.json")


def test_damaged_file_raises(tmp_path):
    with pytest.raises(TranslationDataError, match="cannot read"):
        Translator.load(write(tmp_path, '{"format": 2, "parts": {'))


@pytest.mark.parametrize("content", [
    [1, 2],
    {"something": "else"},
    {"format": 3, "parts": {}},
    {"format": 2},
    {"format": 2, "complete": True, "parts": {"3001": ["BL_3001"]}},
    {"format": 2, "complete": True, "parts": {"3001": {"Bricklunk": ["1"]}}},
    {"format": 2, "complete": True, "parts": {"3001": {"BrickLink": "3001"}}},
])
def test_wrong_shape_raises(tmp_path, content):
    with pytest.raises(TranslationDataError):
        Translator.load(write(tmp_path, content))


def test_incomplete_file_warns_or_raises(tmp_path):
    path = write(tmp_path, v2(complete=False))
    with pytest.warns(UserWarning, match="not marked complete"):
        assert not Translator.load(path).info.complete
    with pytest.raises(TranslationDataError):
        Translator.load(path, require_complete=True)


def test_complete_file_does_not_warn(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Translator.load(write(tmp_path, v2()))


LEGACY = {
    "running_part_count": 200,
    "RB_3001": ["BL_3001", "BO_771344", "LG_15589", "LG_3001"],
    "BL_3001": ["RB_3001", "BO_771344", "LG_15589", "LG_3001"],
    "RB_3001a": ["BL_3001old", "LG_3001"],
    # shared ID: the old builder kept only the last owner
    "LG_3001": ["RB_3001a", "BL_3001old"],
}


def test_legacy_format_loads_from_its_rebrickable_rows(tmp_path):
    with pytest.warns(UserWarning):
        translator = Translator.load(write(tmp_path, LEGACY))
    assert translator.info.format == "legacy" and translator.info.updated is None
    assert translator.info.notes
    assert translator.translate_part("3001", "BrickLink", "BrickOwl") == ["771344"]
    assert translator.translate_part("3001", "LEGO", "Rebrickable") == ["3001", "3001a"]


def test_default_path_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("BRICK_TRANSLATOR_DATA", str(write(tmp_path, v2())))
    monkeypatch.setattr(translator_module, "_default", None)
    assert translator_module.translate_from_to("3001", "BrickLink", "BrickOwl") == ["771344"]


def test_default_path_missing_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("BRICK_TRANSLATOR_DATA", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(translator_module, "_default", None)
    with pytest.raises(TranslationDataError):
        translator_module.translate_from_to("3001", "BrickLink", "BrickOwl")


# The old interface in translate_lib.py


@pytest.fixture
def old(tmp_path, monkeypatch):
    monkeypatch.setenv("BRICK_TRANSLATOR_DATA", str(write(tmp_path, v2())))
    monkeypatch.setattr(translator_module, "_default", None)
    import translate_lib

    return translate_lib


def test_old_from_to(old):
    with pytest.warns(DeprecationWarning):
        assert old.tranlate_from_to("3001", "BrickLink", "BrickOwl") == ["771344"]
        assert old.tranlate_from_to("3001", "BrickLink", "BrickLink") == ["3001"]
        assert old.tranlate_from_to("nope", "BrickLink", "BrickOwl") is False
        with pytest.raises(ValueError):
            old.tranlate_from_to("3001", "BrickLink", "Nowhere")


def test_old_single_scheme_lookups(old):
    with pytest.warns(DeprecationWarning):
        assert old.tranlate_from_rebrickable("3001a") == ["BL_3001old", "LG_3001"]
        assert old.tranlate_from_bricklink("3001old") == ["RB_3001a", "LG_3001"]
        assert old.tranlate_from_lego("3001")[:2] == ["RB_3001", "BL_3001"]
        assert "RB_3001a" in old.tranlate_from_lego("3001")
        assert old.tranlate_from_brickset("15589")[0] == "RB_3001"
        assert old.tranlate_from_brickowl("nope") is False


def test_old_interface_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("BRICK_TRANSLATOR_DATA", str(tmp_path / "absent.json"))
    monkeypatch.setattr(translator_module, "_default", None)
    import translate_lib

    with pytest.warns(DeprecationWarning), pytest.raises(TranslationDataError):
        translate_lib.tranlate_from_rebrickable("3001")
