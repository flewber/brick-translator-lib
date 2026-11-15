import json

import pytest

from brick_translator import Translator
from brick_translator.build import (
    BuildError, build, color_entry, load_state, new_state, part_entry,
    read_part_numbers, save_state,
)

CSV = "part_num,name,part_cat_id,part_material\n" + "".join(f"p{i},Part {i},1,Plastic\n" for i in range(7))


def api_part(number, **external):
    return {"part_num": number, "name": "x", "external_ids": external}


class FakeApi:
    def __init__(self, missing=(), fail_on_call=None):
        self.calls, self.missing, self.fail_on_call = [], set(missing), fail_on_call

    def parts(self, numbers):
        self.calls.append(list(numbers))
        if self.fail_on_call == len(self.calls):
            raise ConnectionError("network down")
        return [api_part(n, BrickLink=[n.upper()], Brickset=[n + "s"]) for n in numbers if n not in self.missing]

    def colors(self):
        return [{"id": 0, "name": "Black", "external_ids": {
            "BrickLink": {"ext_ids": [11], "ext_descrs": [["Black"]]},
            "LEGO": {"ext_ids": [26, 149], "ext_descrs": [["Black"], ["Metallic Black"]]},
            "Unknown site": {"ext_ids": [1]},
        }}]


@pytest.fixture
def parts_csv(tmp_path):
    path = tmp_path / "parts.csv"
    path.write_text(CSV)
    return path


def test_read_part_numbers(parts_csv):
    numbers, digest = read_part_numbers(parts_csv)
    assert numbers == [f"p{i}" for i in range(7)] and len(digest) == 64


def test_read_part_numbers_finds_column_by_name(tmp_path):
    path = tmp_path / "parts.csv"
    path.write_text("name,part_num\nBrick,3001\n")
    assert read_part_numbers(path)[0] == ["3001"]
    path.write_text("name,number\nBrick,3001\n")
    with pytest.raises(BuildError):
        read_part_numbers(path)


def test_part_entry_uses_the_api_key_names():
    entry = part_entry(api_part("3001", BrickLink=["3001"], Brickset=["15589", 3001], LDraw=["3001"],
                                 Peeron=["x"], BrickOwl=[]))
    assert entry == {"BrickLink": ["3001"], "Brickset": ["15589", "3001"], "LDraw": ["3001"]}
    assert part_entry({"part_num": "x"}) == {}


def test_color_entry_accepts_both_shapes():
    api = FakeApi().colors()[0]
    assert color_entry(api) == {"name": "Black", "BrickLink": ["11"], "LEGO": ["26", "149"]}
    assert color_entry({"id": 1, "name": "Blue", "external_ids": {"BrickLink": [7]}}) == {"name": "Blue", "BrickLink": ["7"]}


def test_full_build_loads_in_the_translator(parts_csv, tmp_path):
    numbers, digest = read_part_numbers(parts_csv)
    out = tmp_path / "out.json"
    api = FakeApi()
    state = build(numbers, new_state(digest, len(numbers)), api.parts, api.colors,
                  save=lambda s: save_state(out, s), batch=3)
    assert [len(c) for c in api.calls] == [3, 3, 1]  # no empty request at the end
    assert state["complete"] and state["next_row"] == 7 and state["not_returned"] == []
    translator = Translator.load(out, require_complete=True)
    assert translator.translate_part("P4", "BrickLink", "Brickset") == ["p4s"]
    assert translator.translate_color(11, "BrickLink", "LEGO") == ["26", "149"]
    assert translator.info.updated and translator.info.source


def test_part_count_divisible_by_batch_makes_no_extra_request(parts_csv):
    numbers, digest = read_part_numbers(parts_csv)
    api = FakeApi()
    build(numbers[:6], new_state(digest, 6), api.parts, batch=3)
    assert [len(c) for c in api.calls] == [3, 3]


def test_parts_the_api_does_not_return_are_recorded(parts_csv):
    numbers, digest = read_part_numbers(parts_csv)
    api = FakeApi(missing={"p1", "p5"})
    state = build(numbers, new_state(digest, len(numbers)), api.parts, batch=3)
    assert state["not_returned"] == ["p1", "p5"]
    assert "p1" not in state["parts"] and len(state["parts"]) == 5


def test_unasked_part_in_reply_is_an_error(parts_csv):
    numbers, digest = read_part_numbers(parts_csv)
    with pytest.raises(BuildError):
        build(numbers, new_state(digest, len(numbers)), lambda n: [api_part("other")], batch=3)


def test_interrupted_build_resumes_where_it_stopped(parts_csv, tmp_path):
    numbers, digest = read_part_numbers(parts_csv)
    out = tmp_path / "out.json"
    api = FakeApi(fail_on_call=2)
    with pytest.raises(ConnectionError):
        build(numbers, load_state(out, digest, len(numbers)), api.parts,
              save=lambda s: save_state(out, s), batch=3)
    saved = json.loads(out.read_text())
    assert saved["next_row"] == 3 and not saved["complete"]
    with pytest.warns(UserWarning):
        assert Translator.load(out).info.part_count == 3

    api = FakeApi()
    state = build(numbers, load_state(out, digest, len(numbers)), api.parts,
                  save=lambda s: save_state(out, s), batch=3)
    assert api.calls == [["p3", "p4", "p5"], ["p6"]]
    assert state["complete"] and len(state["parts"]) == 7


def test_resume_with_a_different_parts_csv_is_refused(parts_csv, tmp_path):
    numbers, digest = read_part_numbers(parts_csv)
    out = tmp_path / "out.json"
    save_state(out, new_state(digest, len(numbers)))
    with pytest.raises(BuildError, match="different parts.csv"):
        load_state(out, "0" * 64, len(numbers))


def test_resume_refuses_a_file_it_does_not_understand(tmp_path):
    out = tmp_path / "out.json"
    out.write_text('{"running_part_count": 100}')
    with pytest.raises(BuildError):
        load_state(out, "0" * 64, 1)
    out.write_text("{")
    with pytest.raises(BuildError):
        load_state(out, "0" * 64, 1)


def test_save_leaves_no_temporary_file(tmp_path):
    out = tmp_path / "out.json"
    save_state(out, new_state("0" * 64, 0))
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"]
