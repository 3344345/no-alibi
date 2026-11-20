"""Real 4.2.2 checkpoint and the journal evidence of field-investigation routes."""

from functools import cache

import pytest

from game.chronicle import Book, Branch, ChronicleStore, Command
from game.store import GameStore
from game.witness_late import CHAPTERS
from tests.test_bian_sky import CAST_422


def walk(store, view, path):
    for key in path.split():
        view = store.choose(
            view["id"],
            Command(
                command_id=f"now-{view['revision']}",
                revision=view["revision"],
                choice=key,
            ),
        )
    return view


def test_pre_expansion_printer_desk_can_fork_without_changing_old_destination(tmp_path):
    archive = {
        "format": "juzhongshi-chronicle/3",
        "campaign": "witness",
        "start_chapter": "witness_gao",
        "id": "ac" * 16,
        "name": "走田埂",
        "chapters": ["witness_" + c for c in CAST_422.split()],
        "commands": [
            {"revision": i, "command_id": f"orig-{i}", "choice": key}
            for i, key in enumerate(("go_farmland", "repeat_test"))
        ],
        "checksum": "5a2b82e18bdafdda94b814d3edc9ec2e56d31210a03a9a8dd22699fdb9a44e2a",
    }
    s = ChronicleStore(GameStore(tmp_path / "g"))
    v = s.restore(archive)
    assert v["scene"]["id"] == "copy"
    alternate = s.fork(v["id"], Branch(revision=2))
    assert walk(s, v, "public_watering")["scene"]["id"] == "december"
    assert walk(s, alternate, "bank_again")["scene"]["id"] == "bank_ridge"


@pytest.mark.parametrize(
    "early,later,final,absent",
    [
        (
            "bank_up bank_boy bank_witness bank_one bank_join bank_ride bank_return bank_paired bank_payline",
            "bank_hand bank_pass_mason bank_free",
            "bank_end_byline",
            None,
        ),
        (
            "bank_down bank_follow_well bank_trace bank_why bank_irrigate bank_lend bank_reply bank_blank bank_delay",
            "bank_correct bank_dad bank_real",
            "bank_end_source",
            "bank_end_returns",
        ),
        (
            "bank_down bank_follow_boy bank_trace bank_two bank_cross bank_irrigate bank_last bank_return bank_chain bank_print",
            "bank_hand bank_pass_bounds bank_real",
            "bank_end_returns",
            None,
        ),
        (
            "bank_up bank_measure bank_trace bank_two bank_zero bank_join bank_stay bank_reply bank_blank bank_print",
            "bank_correct bank_walkabout bank_real",
            "bank_end_appeal",
            None,
        ),
        (
            "bank_down bank_follow_well bank_witness bank_why bank_irrigate bank_last bank_reply bank_chain bank_print",
            "bank_correct bank_dad bank_free",
            "bank_end_desk",
            "bank_end_byline",
        ),
        (
            "bank_up bank_measure bank_trace bank_one bank_join bank_stay bank_return bank_paired bank_delay",
            "bank_hand bank_pass_bounds bank_free",
            "bank_end_field",
            None,
        ),
    ],
)
def test_fieldwork_changes_later_options_and_can_be_resumed(
    tmp_path, early, later, final, absent
):
    s = ChronicleStore(GameStore(tmp_path / "a"))
    v = walk(s, s.create("走田埂", "witness", "witness_gao"), "bank_long " + early)
    assert v["scene"]["id"] == "bank_letters"
    if "bank_one" in early:
        entry = next(
            e for e in v["journal"] if e["label"].startswith("两条路抵达同一个缺口")
        )
        assert {x["id"] for x in entry["citations"]} == {"south", "north"}
        assert "两条田埂的草图" in v["scene"]["body"]
    if "bank_paired" in early:
        entry = next(
            e for e in v["journal"] if e["label"].startswith("写清受检池雨后有积水")
        )
        assert {x["id"] for x in entry["citations"]} == {"level", "outlet"}
    second = ChronicleStore(GameStore(tmp_path / "b"))
    loaded = second.restore(s.export(v["id"]))
    assert loaded == v
    ending = walk(second, loaded, later)
    if absent:
        assert absent not in {c["id"] for c in ending["scene"]["choices"]}
    v = walk(second, ending, final)
    assert v["chapter"]["id"] != "witness_gao"
    assert v["journal"][-1]["marks"][0].startswith("结局 · ")


def test_depth_and_resolvable_field_evidence():
    chapter = next(c for c in CHAPTERS if c["id"] == "witness_gao")
    scenes = Book([chapter], "witness").scene_maps[0]

    @cache
    def depths(key):
        if key == "END":
            return {0}
        return {d + 1 for c in scenes[key].choices for d in depths(c.next)}

    assert min(depths("bank_ridge")) >= 12
    assert len([key for key in scenes if key.startswith("bank_")]) == 18
