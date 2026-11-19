"""Time conflicts, independent hypotheses and recoverable losses on player routes."""

import pytest

from tests.test_world_v4 import Play, D, Q


def test_opening_meeting_and_round_trip_compete_for_the_same_deadline():
    def desk_work():
        return Play().do("compare").wait(25).do("revise").wait(30)

    field = desk_work()
    deadline = next(t["due"] for t in field.s["queue"] if t["kind"] == "window_due")
    field.go("L02").do("observe").wait(30).go("L01").do("reply", mode="conditional")
    assert "OBS-site" in field.d["docs"] and field.s["minute"] < deadline
    field.wait(deadline - field.s["minute"])
    assert any("汇总了你已递交的意见" in e["text"] for e in field.log)

    meeting = desk_work().do("report", mode="full")
    with pytest.raises(ValueError):
        meeting.do("travel", location="L02")
    meeting.wait(45).go("L02").do("observe").wait(30).go("L01")
    assert {"OBS-site", "D01-brief"} <= meeting.d["docs"].keys()
    assert meeting.s["minute"] > deadline
    assert any("南渠意见列作待补" in e["text"] for e in meeting.log)


def test_unverified_hypothesis_and_recoverable_loss_of_source():
    g = Play()
    original = g.d["variant"].copy()
    g.do("write_sourced_note", text="我推测整条南渠全部完工。", document="D01-r1",
         classification="个人推测")
    g.do("leave_note").go("L02")
    with pytest.raises(ValueError):
        g.do("copy_note")
    g.do("observe").wait(30).do("evidence").wait(180)
    assert g.d["variant"] == original and g.d["docs"]["D01-detail"]["body"] == original["answer"]
    g.go("L01").do("take_note").do("copy_note").wait(180)
    assert g.d["notebook"]["copies"][0]["entries"] == g.d["notebook"]["entries"]
    assert not g.d["investigation"]["findings"]


@pytest.mark.parametrize(("reason", "ending"), [("leave", "END02"), ("transfer", "END04")])
def test_twelve_completed_quarters_allow_two_noninvestigative_endings(reason, ending):
    g = Play().wait(12 * Q)
    assert g.d["quarter"] == 13 and not g.d["ended"]
    g.do("career_exit", reason=reason).wait(2 * D)
    if reason == "transfer":
        g.do("stage_end", id=ending)
    assert g.d["ending"]["id"] == ending and not g.d["investigation"]["findings"]


@pytest.mark.parametrize("index", range(24))
def test_twenty_four_opening_seeds_can_deliver_the_first_safe_crossing(index):
    from game import engine

    start = f"S{index % 8 + 1:02}"
    g = Play(start=start, seed=f"opening-route-{index:02}")
    g.do("start_channel").wait(150).go("L02").do("observe").wait(30)
    g.do("evidence").wait(250)
    seen = engine.player_view(g.s)
    assert {"OBS-site", "D01-detail"} <= {doc["id"] for doc in seen["documents"]}
    # Choose only what the player's current menu offers; some routes need
    # a repair and a second inspection before the supervisor may approve.
    steps = []
    for _ in range(5):
        options = [a for a in seen["actions"] if a["kind"] == "passage"]
        assert len(options) == 1
        step = options[0]["args"]["step"]
        steps.append(step)
        g.do("passage", step=step).wait(150)
        seen = engine.player_view(g.s)
        if step == "open":
            break
    assert steps in (["inspect", "approve", "open"], ["inspect", "repair", "inspect", "approve", "open"])
    assert g.d["passage"]["opened"] and g.d["promises"]["PR1"]["status"] == "已履约"
    assert g.s["minute"] < Q and not g.d["ended"]


@pytest.mark.parametrize("balance", ["0.000000", "0.250000", "0.500000", "0.750000", "1.000000"])
def test_trusted_technician_can_keep_the_appointment_and_deliver_accurate_evidence(balance):
    g = Play(seed="classic", balance=balance)
    g.wait(2 * D).do("technician", mode="retain").wait(4 * D)
    assert g.d["technical_rotation"]["state"] == "留任完成检查"
    g.go("L02").do("evidence").wait(250)
    doc = g.d["docs"]["D01-detail"]
    assert doc["body"] == g.d["variant"]["answer"]
    source = next(e for e in g.log if e["id"] in doc["refs"])
    assert source["actor"] == "N18" and source["visible"]
    g.do("passage", step="inspect").wait(150)
    assert g.d["passage"]["stage"] == "检查通过"
    assert any(e["actor"] == "N18" and e["id"] in g.d["passage"]["checks"] for e in g.log)


def test_same_visible_claim_can_be_ruled_out_or_confirmed_with_dated_records():
    from game import engine

    def player_documents(g):
        return {doc["id"]: doc for doc in engine.player_view(g.s)["documents"]}

    early, later = Play(seed="classic"), Play(seed="0")
    for key in ("D01-r1", "D01-ledger"):
        assert player_documents(early)[key]["body"] == player_documents(later)[key]["body"]
    for g in (early, later):
        assert "D01-detail" not in player_documents(g)
        g.go("L02").do("evidence").wait(250)
    first = player_documents(early)["D01-detail"]
    second = player_documents(later)["D01-detail"]
    assert all(d["refs"] and d["date"] and d["scope"] for d in (first, second))
    assert "同日分项台账合计 20" in first["body"] and "尚未达到完成条件" in first["body"]
    assert "此后新验收了 20" in second["body"] and "最新交接单累计 40" in second["body"]
