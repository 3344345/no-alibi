"""Run the registered starts through the eight endings, including the last decision or deadline."""

import json

import pytest

from game import balance, catalog, engine
from tests.test_world_v4 import D, Q, Play


def before_ending(start, ending):
    # All preparation uses normal commands. Each returned save precedes the last
    # action/receipt, so the ending can also be exercised as a local fixture.
    seed = "19" if ending in ("END07", "END08") else "classic"
    g = Play(start=start, seed=seed)
    if ending == "END01":
        quarters = 4 * (60 - catalog.STARTS[start]["age"])
        while quarters:
            step = min(quarters, 100)
            g.wait(step * Q)
            quarters -= step
        return g, "advance", {"minutes": 120}
    if ending == "END02":
        g.do("career_exit", reason="leave")
        return g, "advance", {"minutes": 2 * D}
    if ending == "END03":
        g.do("invite", choice="yes").go("L04").do("speak", mode="limited")
        g.wait(20).go("L01").wait(4 * Q).do("career_exit", reason="marginal")
        return g, "advance", {"minutes": D}
    if ending == "END04":
        g.do("career_exit", reason="transfer").wait(2 * D)
        return g, "stage_end", {"id": "END04"}
    if ending in ("END05", "END06"):
        g.do("appointment", place="L05").wait(180).go("L05").do("gift", choice="take")
        g.go("L01").do("refer", document="GIFT-take").wait(180)
        g.do("review", mode="origin").wait(3 * D).do("hearing", mode="written").wait(
            300
        )
        if ending == "END05":
            g.do("finding", mode="exit")
            return g, "advance", {"minutes": 120}
        return g, "finding", {"mode": "file"}
    g.wait((g.d["career"]["health_window"] - 1) * Q)
    if ending == "END07":
        g.do("career_exit", reason="care")
        return g, "advance", {"minutes": 3 * D}
    g.wait(5 * D)
    assert g.d["career"]["illness"] == "已取得重病变化通知"
    return g, "advance", {"minutes": 3 * D}


@pytest.mark.parametrize("start", list(catalog.STARTS))
@pytest.mark.parametrize("ending", list(catalog.ENDINGS))
def test_ending_from_registered_start_and_final_checkpoint(start, ending):
    g, kind, args = before_ending(start, ending)
    assert not g.d["ended"] and g.d["ending"] is None
    checkpoint = json.dumps(g.s, ensure_ascii=False)
    cmd = engine.Command(
        command_id=f"r{g.s['revision']}",
        expected_revision=g.s["revision"],
        kind=kind,
        args=args,
    )
    g.do(kind, **args)
    reached = engine.player_view(g.s)["ending"]
    assert (
        reached["id"] == ending
        and reached["resume_policy"] == catalog.ENDINGS[ending]["resume_policy"]
    )
    observed = {event["id"] for event in g.log}
    assert reached["refs"] and set(reached["refs"]) <= observed
    loaded, events = engine.resolve(json.loads(checkpoint), cmd)
    assert balance.canonical(loaded) == balance.canonical(g.s)
    assert balance.canonical(events) == balance.canonical(g.log[-len(events) :])
