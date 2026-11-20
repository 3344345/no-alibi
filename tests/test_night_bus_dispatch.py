"""Board predictions and the decisions they unlock, through the regular career clock."""

import pytest

from game.engine import GameError
from game.store import GameStore
from game.world_night_bus import project, validate
from tests.test_night_bus import choose
from tests.test_world_v4 import Play


FIRST_NIGHT_TO_TRIAL = (
    "stay_curb promise_ma no_tip blanket fuel seal_name ride_watch "
    "count_left separate speak_ma spare_seats"
).split()


@pytest.mark.parametrize("key,arrive,nurses,transfer,travel,target,after,document,memory", [
    ("bridge_0", "22:53", 0, True, 13, "dispatch_platform", "dispatch_call_ward", "night_phone", "分机号"),
    ("bridge_6", "22:59", 1, True, 19, "dispatch_doors", "dispatch_lost_shelf", "shelf", "线手套"),
    ("bridge_12", "23:05", 3, False, 25, "dispatch_late", "dispatch_bed", "folding_bed", "旧路书"),
    ("baths_0", "22:58", 1, True, 18, "dispatch_doors", "dispatch_return_tin", "tin_return", "詹叔"),
    ("baths_6", "23:04", 3, False, 24, "dispatch_late", "dispatch_sunrise", "bread_slip", "面粉印"),
    ("baths_12", "23:10", 3, False, 30, "dispatch_late", "dispatch_bed", "folding_bed", "旧路书"),
])
def test_timetable_lives_on_in_the_county(key, arrive, nurses, transfer, travel, target, after, document, memory):
    player = Play()
    choose(player, "dial_paper")
    assert not any(plan["marked"] for plan in project(player.d)["dispatch"])
    choose(player, "paper_" + key)
    assert "男孩认出了你的声音" in project(player.d)["body"]
    for choice in FIRST_NIGHT_TO_TRIAL + ["dial_live"]:
        choose(player, choice)
    live = "run_" + key
    plans = project(player.d)["dispatch"]
    assert [p["key"] for p in plans if p["marked"]] == [live]
    plan = next(p for p in plans if p["key"] == live)
    assert (plan["arrive"], plan["nurses"], plan["transfer"]) == (arrive, nurses, transfer)
    assert bool(plan["bath_at"]) == key.startswith("baths")
    before = player.s["minute"]
    player.do("night_bus", scene="dispatch_live", choice=live)
    assert project(player.d)["due"] == before + travel
    assert "调度单" in project(player.d)["reply"]
    with pytest.raises(GameError):
        player.do("night_bus", scene=target, choice=after)
    player.wait(travel - 1)
    assert project(player.d)["stage"] == "waiting"
    validate(player.d)
    player.wait(1)
    assert player.d["night_bus"]["node"] == target
    assert arrive in project(player.d)["reply"]
    assert ("赶紧往前门挪" in project(player.d)["reply"]) == transfer
    choose(player, after)
    assert document in {doc.removeprefix("BUS-") for doc in player.d["docs"]}
    assert arrive in project(player.d)["body"]
    for choice in ["follow_line", "pay_shift"]:
        choose(player, choice)
    assert memory in project(player.d)["body"]
    choose(player, "co_op")
    choose(player, "end_contract")
    validate(player.d)
    assert player.d["night_bus"]["node"] == "end_contract"


def test_rehearsal_can_be_reloaded_and_overridden(tmp_path):
    store = GameStore(tmp_path / "test.sqlite")
    view = store.create()
    wid = view["world_id"]

    def go(kind, args):
        nonlocal view
        rev = view["revision"]
        view = store.execute(wid, f"c{rev}", rev, kind, args)

    def commit(key):
        args = next(a["args"] for a in view["actions"] if a["args"].get("choice") == key)
        go("night_bus", args)

    def arrive():
        while view["night_bus"]["due"] is not None:
            go("advance", {"minutes": view["night_bus"]["due"] - view["minute"]})

    for key in ["dial_paper", "paper_baths_6", *FIRST_NIGHT_TO_TRIAL, "dial_live", "run_bridge_0"]:
        arrive()
        commit(key)
    assert view["night_bus"]["stage"] == "waiting"
    reopened = GameStore(tmp_path / "restore.sqlite")
    restored = reopened.restore(store.export(wid))
    assert restored["night_bus"] == view["night_bus"]
    due = restored["night_bus"]["due"]
    arrived = reopened.execute(restored["world_id"], "arrive", restored["revision"], "advance",
                               {"minutes": due - restored["minute"]})
    assert "22:53" in arrived["night_bus"]["reply"]
    assert arrived["night_bus"]["title"] == "还剩七分钟"
