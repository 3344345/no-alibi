"""Historical C/F pathways on the real offline command, SQLite, delivery and replay paths."""

import json
from copy import copy
import pytest
from ai.player_intent import parse_visible
from game.catalog import DAY, QUARTER, WAN
from game.store import GameStore


class Journey:
    def __init__(self, path, start="S01"):
        self.store = GameStore(path / "journey.db")
        self.v = self.store.create(start, "周林", "0.500000", "classic")
        self.world = self.v["world_id"]
        self.last = None

    @property
    def d(self):
        with self.store._db() as db:
            return json.loads(self.store._world(db, self.world)["projection"])["domain"]

    def do(self, kind, **args):
        seq = self.v["revision"]
        cid = "cmd-" + str(seq)
        self.last = (self.world, cid, seq, kind, args)
        self.v = self.store.execute(*self.last)
        return self

    def wait(self, minutes):
        return self.do("advance", minutes=minutes)

    def go(self, place):
        self.do("travel", location=place)
        self.wait(self.d["busy"]["player"]["due"] - self.v["minute"])
        assert self.v["location"]["id"] == place
        return self

    def events(self):
        return [
            e
            for record in self.store.export(self.world)["history"]
            for e in record["events"]
        ]

    def verify(self):
        assert self.store.replay(self.world) and self.v == self.store.view(self.world)
        restored = self.store.restore(self.store.export(self.world))
        assert restored["revision"] == self.v["revision"]


def test_c01_f01_skip_real_three_week_delay_then_resource_conflict(tmp_path):
    j = Journey(tmp_path)
    s = j.d["field_schedule"]
    assert s["forecast"] - s["planned"] == 21 * DAY
    for who, text in [("N08", "迟三周"), ("N02", "仍按原窗口")]:
        person = j.d["actors"][who]
        ref = person["belief_topics"]["initial_schedule"]
        assert text in person["beliefs"][ref]
    assert "迟三周" not in json.dumps(j.v, ensure_ascii=False)
    before = j.v["player"]["pressure"]
    j.do("report", mode="skip")
    assert j.v["player"]["pressure"] == before and not j.d["flags"].get("recovery_ref")
    j.wait(90).go("L03").do("department_round").wait(50)
    rows = j.d["department_round"]["bids"]
    assert (
        sum(r["groups"] for r in rows.values())
        == 14
        > j.v["finances"]["groups_available"]
    )
    bid = next(e for e in j.events() if e["id"] == rows["P01"]["source"])
    assert j.d["flags"]["recovery_ref"] in bid["refs"] and "补救延期" in bid["text"]
    j.verify()


def test_c02_private_meeting_parser_and_disclosed_or_refused(tmp_path):
    j = Journey(tmp_path)
    parsed = parse_visible("请私下核实现场排期", j.v)
    assert (
        parsed["status"] == "parsed" and parsed["options"][0]["kind"] == "private_check"
    )
    j.do("private_check").wait(120).go("L02").do("private_meeting").wait(25)
    assert (
        j.d["flags"]["private_check"] == "实际到场"
        and j.d["field_schedule"]["holder"] == "N08"
    )
    assert not any(
        "技术员本人参与了本次核实" in x
        for x in j.d["actors"]["N08"]["beliefs"].values()
    )
    j.wait(180)
    assert any(
        "技术员本人参与了本次核实" in x
        for x in j.d["actors"]["N08"]["beliefs"].values()
    )
    j.verify()
    j = Journey(tmp_path)
    j.wait(6 * DAY)
    assert "N18" in j.d["busy"]
    j.do("private_check").wait(150)
    assert j.d["flags"]["private_check"] == "未能赴约"
    assert not any(e["title"] == "现场核实排期" for e in j.events())
    j.verify()


def test_c03_f04_independent_same_minute_department_claims_and_replan(tmp_path):
    j = Journey(tmp_path)
    j.go("L03").do("department_round").wait(50)
    bids = j.d["department_round"]["bids"]
    assert {r["applicant"] for r in bids.values()} == {"N07", "N08", "N09"}
    events = {e["id"]: e for e in j.events()}
    assert len({events[r["source"]]["minute"] for r in bids.values()}) == 1
    assert (
        sum(r["request"] for r in bids.values())
        == 2400 * WAN
        > j.v["finances"]["quarter_remaining"]
    )
    j.do("propose", plan="C").wait(150).do("offer", offer="OF-1", choice="accept")
    same = j.store.execute(*j.last)
    assert same == j.v
    j.wait(180)
    assert "改列下一窗口，保留未获配任务。" in j.d["actors"]["N07"]["plans"]
    assert j.v["finances"]["paid"] <= 400 * WAN and j.v["finances"]["reserved"] == 0
    j.verify()


def test_c04_f07_old_channel_transfers_then_allied_interests_change(tmp_path):
    j = Journey(tmp_path, start="S06")
    dep = j.d["actors"]["N03"]["relations"]["N12"]["dependency"]
    j.wait(4 * DAY)
    assert "交回原联络岗位" in " ".join(j.d["actors"]["N12"]["beliefs"].values())
    assert j.d["actors"]["N03"]["relations"]["N12"]["dependency"] == dep
    assert "N12" not in j.d["roles"]
    j.wait(240)
    assert j.d["actors"]["N03"]["relations"]["N12"]["dependency"] < dep
    assert j.d["roles"]["N12"] == "调任后的顾问"
    j.do("mentor_channel", mode="accept").wait(200)
    assert (
        "D07-new-contact" in j.d["docs"]
        and j.d["actors"]["N10"]["relations"]["player"]["dependency"] > 0.1
    )
    j.verify()


def test_c05_f02_author_and_auditor_hold_new_version_player_keeps_old(tmp_path):
    j = Journey(tmp_path)
    assert "PLAN-r1" in j.d["docs"] and "PLAN-r2" not in j.d["docs"]
    assert set(j.d["field_schedule"]["received_by"]) == {"N08", "N18"}
    old = j.d["docs"]["PLAN-r1"].copy()
    j.do("audit_schedule").wait(180)
    assert j.d["investigation"]["scheduling_evidence"][-1]["version"] == "PLAN-r2"
    assert "N19" in j.d["field_schedule"]["received_by"]
    assert any("第 29 天" in v for v in j.d["actors"]["N19"]["beliefs"].values())
    assert (
        j.d["docs"]["PLAN-r1"] == old
        and "PLAN-r2" not in j.d["docs"]
        and "AUD-schedule" in j.d["docs"]
    )
    j.verify()


def test_c06_f05_three_promises_and_three_person_echo(tmp_path):
    j = Journey(tmp_path)
    j.go("L07").do("speak", mode="limited").wait(15)
    j.do("invite", choice="yes").go("L04").do("speak", mode="assure").wait(15).go("L01")
    assert len(j.d["promises"]) == 3
    j.wait(3 * DAY)
    events = j.events()
    index = {e["id"]: e for e in events}
    branch = next(e for e in events if e["title"] == "收到转述" and e["actor"] == "N11")
    e2 = index[branch["refs"][0]]
    e1 = index[e2["refs"][0]]
    origin = index[e1["refs"][0]]
    assert (origin["title"], e1["actor"], e2["actor"], branch["actor"]) == (
        "当面原话",
        "N15",
        "N14",
        "N11",
    )
    assert origin["minute"] < e1["minute"] < e2["minute"] < branch["minute"]
    assert origin["text"] != e1["text"] and e2["text"] != e1["text"]
    dues = [e["minute"] for e in events if e["title"] == "承诺到期"]
    assert len(dues) == 3 and dues == sorted(dues) and len(set(dues)) == 3
    assert all(x["status"] == "逾期" for x in j.d["promises"].values())
    j.verify()


def test_c07_f06_removed_original_persists_as_independent_copy(tmp_path):
    j = Journey(tmp_path)
    j.do("write_note", text="个人猜测，等待复核。").do("leave_note").go("L02")
    assert j.v["notebook"]["entries"] == []
    assert not j.d["investigation"]["acquired"]
    j.go("L01").do("take_note").do("copy_note").wait(120).do("destroy_note").do(
        "confirm_note", choice="yes"
    )
    assert j.d["notebook"]["copies"][0]["holder"] == "N19"
    assert j.v["notebook"]["entries"] == [] and not j.d["investigation"]["findings"]
    j.verify()


def test_c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding(
    tmp_path,
):
    j = Journey(tmp_path)
    j.do("appointment", place="L05").wait(180).go("L05").do("gift", choice="take").go(
        "L01"
    )
    j.do("write_note", text="个人推测，这笔礼物可能与资金申请有关。").do(
        "copy_note"
    ).wait(180)
    j.wait(13 * QUARTER)
    assert not j.d["investigation"]["findings"]
    j.do("refer", document="NB-copy-1").wait(180).do("review", mode="origin").wait(220)
    assert (
        j.d["investigation"]["status"] == "已归档"
        and not j.d["investigation"]["findings"]
    )
    j.do("refer", document="GIFT-take").wait(180).do("review", mode="origin").wait(3500)
    assert j.d["investigation"]["hearing"] == "需答复"
    j.do("hearing", mode="written").wait(180).do("finding", mode="file")
    assert j.v["ending"]["id"] == "END06" and j.v["quarter"] >= 14
    refs = {e["id"]: e for e in j.events()}
    finding = j.d["investigation"]["findings"][-1]
    assert "曾收下礼盒" in finding["text"] and "资金申请有关" not in finding["text"]
    assert all(r in refs for r in refs[finding["ref"]]["refs"])
    j.verify()


def test_separate_jurisdictions_compete_for_a_single_real_pool(tmp_path):
    j = Journey(tmp_path, start="S04")
    j.do("start_channel").wait(100).do("delegate").wait(100).do("revise").wait(60)
    j.go("L03").do("cooperate").wait(60).go("L01")
    for _ in range(48):
        c = j.d["career"]
        rank = c["rank"]
        if rank >= 2 and not c.get("cross_record"):
            box = j.d["regional"][str(rank)]
            assert len(box["received"]) == 2
            j.do("cross_review").wait(90).do("regional_allocate", choice="first").wait(
                250
            )
            box = j.d["regional"][str(rank)]
            assert box["reserved"] == 3 and box["capacity"] == 3
            actual = sum(x["allocated"] for x in box["requests"].values())
            assert actual == 3 < sum(x["requested"] for x in box["requests"].values())
            j.wait(2 * DAY)
            box = j.d["regional"][str(rank)]
            assert (
                box["reserved"] == 0
                and sum(x["served"] for x in box["requests"].values()) == 3
            )
            assert any(
                x["state"] == "未完成部分留待后续" for x in box["requests"].values()
            )
        if rank == 5:
            break
        if c["vacancy"] and not c["applied"]:
            j.do("nominate", mode="self").wait(2 * DAY)
            continue
        j.wait(QUARTER - j.v["minute"] % QUARTER)
    assert j.d["career"]["rank"] == 5
    assert all(x["status"] == "已交付" for x in j.d["regional"].values())
    j.verify()


def test_funding_decisions_from_same_saved_offer_diverge_next_quarter(tmp_path):
    funded = Journey(tmp_path)
    funded.go("L03").do("propose", plan="C").wait(180)
    revised_offer = funded.d["offers"][0]
    deferred = copy(funded)
    deferred.v = funded.store.fork(funded.world, funded.v["revision"])
    deferred.world = deferred.v["world_id"]
    assert deferred.d["offers"][0] == revised_offer
    funded.do("offer", offer="OF-1", choice="accept").wait(10 * DAY)
    funded.do("stage_check", project="P01").wait(300)
    deferred.do("offer", offer="OF-1", choice="withdraw")
    for branch in (deferred, funded):
        branch.wait(QUARTER - branch.v["minute"])
        assert branch.d["quarter"] == 2
        branch.verify()
    open_stage = funded.d["projects"]["P01"]
    assert open_stage["opened"] and open_stage["maintenance_due"]
    assert funded.d["fiscal"]["paid"] == revised_offer["terms"]["P01"]["amount"]
    assert deferred.d["fiscal"]["paid"] == 0
    assert deferred.d["projects"]["P01"]["phase"] == "拟议"
