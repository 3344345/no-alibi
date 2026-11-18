"""Executable positive and negative boundaries for every mechanism in the V4 world pack."""

from tests.test_world_v4 import Play, D, Q
from tests.test_scenario_routes_v4 import reject
from game import catalog, world
from game.world_office import relation


def test_m01_m04_documents_authority_promises_and_versions():
    g = Play()
    for key in ("P02", "P03"):
        g.do("permit", project=key)
        assert (
            g.d["projects"][key]["permit_pending"]
            and not g.d["projects"][key]["permit"]
        )
        reject(g, "permit", project=key)
    reject(g, "authority", mode="sign")
    g.do("authority", mode="request").wait(180)
    g.do("authority", mode="sign").wait(20)
    assert g.d["docs"]["COORD-r1"]["scope"] == "P01 协调分工"
    assert all(k not in g.d["flags"] for k in ("budget_signed", "appointed"))
    reject(g, "commitment", id="missing", mode="deliver")
    g.do("commitment", id="PR1", mode="revise").wait(40)
    assert g.d["promises"]["PR1"]["version"] == 2
    g.wait(3 * D)
    assert g.d["promises"]["PR1"]["status"] == "逾期"
    reject(g, "revise")
    old = g.d["docs"]["D01-r1"].copy()
    g.do("compare").wait(30).do("revise").wait(35)
    assert g.d["docs"]["D01-r2"]["refs"] != old["refs"] and g.d["docs"]["D01-r1"] == old


def test_m05_m08_real_task_execution_reschedule_and_inspect():
    for no_mobilization in (False, True):
        g = Play()
        g.go("L03")
        reject(g, "stage_check", project="P01")
        g.do("propose", plan="C")
        reject(g, "offer", offer="OF-1", choice="accept")
        g.wait(180).do("offer", offer="OF-1", choice="accept")
        p = g.d["projects"]["P01"]
        assert p["phase"] == "预留待进场" and not p["work_done"]
        if no_mobilization:
            g.do("cancel_reservation", project="P01").wait(8 * D)
            assert (
                g.d["fiscal"]["paid"] == 0 and g.d["projects"]["P01"]["phase"] == "拟议"
            )
            continue
        g.wait(80)
        assert g.d["projects"]["P01"]["phase"] == "施工中"
        reject(g, "cancel_reservation", project="P01")
        reject(g, "stage_check", project="P01")
        assert g.d["fiscal"]["paid"] > 0
        g.wait(8 * D).do("stage_check", project="P01").wait(300)
        current = g.d["projects"]["P01"]
        assert (
            current["opened"] and current["checked"] and len(current["approvals"]) == 2
        )


def test_m09_m12_invitations_present_people_speech_and_negotiation():
    for choice in ("yes", "no", "later", "free"):
        g = Play()
        reject(g, "travel", location="L04")
        reject(g, "speak", mode="limited")
        params = {"text": "我会前来。"} if choice == "free" else {}
        g.do("invite", choice=choice, **params)
        reject(g, "invite", choice="yes")
        if choice == "no":
            reject(g, "travel", location="L04")
            continue
        g.do("travel", location="L04")
        assert g.d["location"] == "L01"
        reject(g, "speak", mode="limited")
        g.wait(50).do("speak", mode="limited").wait(15)
        speech = g.d["statements"][-1]
        assert (
            speech["audience"] == ["N17"]
            and speech["ref"] not in g.d["actors"]["N19"]["beliefs"]
        )
    h = Play()
    h.go("L03").do("propose", plan="B").wait(180)
    reject(h, "offer", offer="OF-1", choice="accept")
    h.do("offer", offer="OF-1", choice="withdraw")
    assert h.d["offers"][0]["status"] == "撤回" and h.d["fiscal"]["reserved"] == 0


def test_m13_m16_subjective_network_changes_are_local_and_causal():
    g = Play()
    reject(g, "consult", npc="N17", mode="normal")
    g.do("consult", npc="N11", mode="normal").wait(15)
    assert (
        relation(g.d, "N11")["familiarity"] > 0.35
        and "player" not in g.d["actors"]["N03"]["relations"]
    )
    reject(g, "favour", id="fictional", mode="help")
    g.go("L03").do("cooperate").wait(200)
    fav = next(iter(g.d["favours"].values()))
    assert fav["from"] == "N03" and g.d["flags"]["cooperate"]
    g.do("favour", id=fav["id"], mode="help").wait(30)
    assert g.d["favours"][fav["id"]]["state"] == "已提交目录"
    g.wait(4 * D + 240)
    assert g.d["actors"]["N03"]["relations"]["N12"]["dependency"] < 0.45
    reject(g, "gift", choice="take")
    g.go("L01").do("appointment", place="L05").wait(160).go("L05").do(
        "gift", choice="take"
    )
    assert (
        relation(g.d, "N17")["shared_exposure"] > 0
        and relation(g.d, "N03")["shared_exposure"] == 0
    )
    assert not g.d["investigation"]["findings"]


def test_m17_m20_tenure_authority_finite_crews_and_expiry():
    g = Play()
    reject(g, "nominate", mode="self")
    g.wait(4 * Q)
    g.do("nominate", mode="self").wait(2 * D)
    assert (
        g.d["career"]["rank"] == 0 and g.d["career"]["positions"]["POS-C1"] != "player"
    )
    g.do("career_exit", reason="transfer")
    assert not g.d["career"]["transferred"]
    due = next(t["due"] for t in g.s["queue"] if t["kind"] == "handover")
    g.wait(due - g.s["minute"])
    assert g.d["career"]["transferred"] and not g.d["ended"]
    g.do("authority", mode="request").wait(D).do("authority", mode="release")
    reject(g, "authority", mode="sign")
    h = Play()
    h.go("L03")
    for key in ("P02", "P03"):
        h.do("permit", project=key)
    h.wait(2 * D).do("propose", plan="B").wait(180).do(
        "offer", offer="OF-1", choice="accept"
    )
    assert sum(h.d["fiscal"]["groups"].values()) == 12
    reject(h, "offer", offer="OF-1", choice="accept")
    h.wait(10 * D)
    assert sum(h.d["fiscal"]["groups"].values()) == 0


def test_m21_m24_messages_testimony_independent_checks_and_clarification():
    g = Play()
    reject(g, "clarify")
    reject(g, "inquire", npc="N24")
    g.go("L07").do("speak", mode="limited").wait(15)
    spoke = g.d["statements"][0]["ref"]
    assert (
        spoke in g.d["actors"]["N15"]["beliefs"]
        and spoke not in g.d["actors"]["N14"]["beliefs"]
    )
    assert not any(k.startswith("RELAY-") for k in g.d["docs"])
    g.wait(350).do("clarify").wait(180)
    assert (
        any(k.startswith("CLARIFY-") for k in g.d["docs"])
        and g.d["cases"]["K11"]["status"] == "resolved"
    )
    g.go("L01").do("evidence")
    assert "D01-detail" not in g.d["docs"]
    g.wait(180)
    assert g.d["docs"]["D01-detail"]["source_id"] == "N18"


def test_m25_m28_no_finding_from_a_lead_and_source_bound_case_result():
    g = Play()
    reject(g, "review", mode="origin")
    reject(g, "hearing", mode="attend")
    g.do("write_note", text="亲属的说法暂未核实").do("copy_note").wait(180)
    g.do("refer", document="NB-copy-1")
    assert not g.d["investigation"]["acquired"] and not g.d["investigation"]["findings"]
    g.wait(180).do("review", mode="origin").wait(180)
    assert (
        g.d["investigation"]["status"] == "已归档"
        and not g.d["investigation"]["findings"]
    )
    reject(g, "finding", mode="exit")
    g.do("appointment", place="L05").wait(180).go("L05").do("gift", choice="take").go(
        "L01"
    )
    g.do("refer", document="GIFT-take").wait(180).do("review", mode="origin").wait(D)
    assert world.decision_pending(g.d) and not g.d["investigation"]["findings"]
    g.do("hearing", mode="written").wait(180)
    finding = g.d["investigation"]["findings"][-1]
    assert finding["ref"] and "曾收下礼盒" in finding["text"]


def test_m29_m32_family_rest_confirmed_attempt_and_lawful_ending():
    g = Play()
    reject(g, "family_plan", mode="cover")
    g.go("L07").do("family_plan", mode="share").wait(40)
    for _ in range(5):
        g.do("rest").wait(45)
    assert g.d["family"]["resilience"] == 72 and g.d["family"]["fatigue"] == 0
    assert not g.d["ended"] and not g.d["investigation"]["findings"]
    g.do("present_item", item="restricted")
    assert any(e["kind"] == "AttemptUnfulfilled" for e in g.log) and not g.d["ended"]
    reject(g, "present_item", item="invented")
    reject(g, "stage_end", id="END08")
    g.go("L01").do("career_exit", reason="leave").wait(2 * D)
    assert g.d["ending"]["id"] == "END02" and g.d["ending"]["refs"]
    reject(g, "rest")
