"""Play the serial through the regular career resolver, calendar and save stack."""

import pytest

from game.engine import GameError
from game.night_bus_story import ECHOES, EXHIBITS, SCENES
from game.store import GameStore
from tests.test_world_v4 import Play


def choose(play, key):
    from game.world_night_bus import options

    by_key = {a["args"]["choice"]: a for a in options(play.d)}
    assert key in by_key, by_key.keys()
    play.do("night_bus", **by_key[key]["args"])
    while (due := play.d["night_bus"].get("due")) is not None:
        play.wait(due - play.s["minute"])


@pytest.mark.parametrize(
    "options,finals",
    [
        (
            "stay_curb promise_ma no_tip pliers imprint seal_name ride_watch count_left float speak_ma spare_seats hold write_miss inspect_stubs classify proof_line pay_shift co_op end_commons",
            "end_light",
        ),
        (
            "take_seat roll reserve_price blanket fuel release_name depot_watch signed_keeper separate speak_child relief on_time bell follow_money assign_debt sell end_strip",
            "end_strip",
        ),
        (
            "stay_curb copy_gate no_tip pliers take_pliers seal_name depot_watch photo_hook float speak_drivers doors hold shift_bridge inspect_stubs accuse_riders correct_count proof_debt name_cost audit end_repay",
            "end_count",
        ),
        (
            "take_seat ask_daughter reserve_price blanket sit_van release_name ride_watch record_voice float speak_child mother_drives on_time layby inspect_stubs accuse_van correct_van proof_line rota bridge_deal end_extend",
            "end_chalk",
        ),
        (
            "stay_curb promise_ma no_tip blanket fuel seal_name ride_watch count_left separate speak_ma full_seats on_time layby follow_line pay_shift co_op end_contract",
            "end_contract",
        ),
        (
            "take_seat ask_daughter no_tip pliers take_pliers release_name ride_watch record_voice separate speak_drivers insure hold write_miss follow_money name_cost sell end_depot",
            "end_north",
        ),
        (
            "take_seat roll reserve_price pliers imprint seal_name ride_watch count_left separate speak_drivers doors hold shift_bridge follow_money assign_debt audit end_pause",
            "end_lantern",
        ),
    ],
)
def test_play_to_seven_distinct_endings(options, finals):
    p = Play()
    for key in ["arrange", *options.split()]:
        choose(p, key)
    assert p.d["night_bus"]["node"] == finals
    assert "BUS-conclusion" in p.d["docs"]
    assert not p.d["ended"]
    assert p.s["minute"] > 30 * 1440
    # Finish the optional serial and return to the original simulation.
    p.do("compare").wait(80)


def test_calendar_and_physical_evidence_survive_fork_restore(tmp_path):
    store = GameStore(tmp_path / "county.sqlite")
    v = store.create()
    wid = v["world_id"]
    assert v["night_bus"]["stage"] == "invitation"
    args = {"scene": "call", "choice": "arrange"}
    v = store.execute(wid, "answer", 0, "night_bus", args)
    assert store.execute(wid, "answer", 0, "night_bus", args) == v
    assert v["night_bus"]["stage"] == "waiting"
    assert v["night_bus"]["due"] == 820
    assert "铁盒" not in v["night_bus"]["body"]
    assert len([a for a in v["appointments"] if a["title"] == "南门旧站牌碰面"]) == 1
    other = GameStore(tmp_path / "other.sqlite")
    loaded = other.restore(store.export(wid))
    assert loaded["night_bus"] == v["night_bus"]
    forked = store.fork(wid, v["revision"])
    assert forked["night_bus"] == v["night_bus"]
    with pytest.raises(GameError):
        store.execute(
            wid, "tooearly", 1, "night_bus", {"scene": "curb", "choice": "take_seat"}
        )
    arrived = store.execute(wid, "visit", 1, "advance", {"minutes": 820})
    assert arrived["night_bus"]["title"] == "车门只开了一半"
    assert store.view(forked["world_id"])["night_bus"]["stage"] == "waiting"


def test_canal_detour_requires_completed_original_project():
    p = Play()
    for key in (
        "arrange stay_curb promise_ma no_tip blanket fuel seal_name ride_watch count_left separate speak_ma spare_seats"
    ).split():
        choose(p, key)
    with pytest.raises(GameError):
        p.do("night_bus", scene="trial", choice="canal_link")
    p.go("L02")
    for step in ("inspect", "approve", "open"):
        p.do("passage", step=step).wait(150)
    choose(p, "canal_link")
    choose(p, "canal_lit")
    assert "BUS-canal" in p.d["docs"]


def test_all_story_links_choices_and_exhibits():
    keys = [c.key for n in SCENES.values() for c in n.choices]
    assert len(keys) == len(set(keys))
    for n in SCENES.values():
        for c in n.choices:
            assert c.target in SCENES
            assert not c.exhibit or c.exhibit in EXHIBITS
            assert (
                not c.needs
                or c.needs == "county:passage"
                or set(c.needs.split("|")) <= set(keys)
            )
    for node, variants in ECHOES.items():
        assert node in SCENES and variants.keys() <= set(keys)
