"""A07. Due tasks on both sides of a quarter and a mandatory hearing."""

import json

import pytest

from game.catalog import DAY, QUARTER
from tests.test_cross_system_routes import Journey


def test_three_deadlines_cross_quarter_and_pause_before_later_work(tmp_path):
    j = Journey(tmp_path)
    j.do("appointment", place="L05").wait(180).go("L05").do("gift", choice="take")
    j.go("L01").do("refer", document="GIFT-take").wait(180)
    j.wait(QUARTER - 70 - j.v["minute"])
    j.do("review", mode="origin").do("private_check").do("delegate").do("evidence")
    j.do("permit", project="P02")
    with j.store._db(snapshot=True) as db:
        state = json.loads(j.store._world(db, j.world)["projection"])
    due = {t["kind"]: t["due"] for t in state["queue"]}
    assert due["delegate"] < due["private_reply"] < QUARTER < due["evidence"]
    j.wait(5 * DAY)
    log = j.events()
    for kind, title in (
        ("delegate", "两份材料的日期与范围"),
        ("private_reply", "非公开联络答复"),
        ("evidence", "工程量清单"),
    ):
        assert [e["minute"] for e in log if e["title"] == title] == [due[kind]]
    hearing = next(e for e in log if e["title"] == "待本人答复")
    assert due["evidence"] < hearing["minute"] == j.v["minute"] < due["permit_done"]
    assert j.d["quarter"] == 2 and not j.d["projects"]["P02"]["permit"]
    with pytest.raises(ValueError, match="决定"):
        j.wait(5 * DAY)
    assert j.v == j.store.view(j.world)
    j.do("hearing", mode="written").wait(due["permit_done"] - j.v["minute"])
    assert j.d["projects"]["P02"]["permit"]
    j.verify()
