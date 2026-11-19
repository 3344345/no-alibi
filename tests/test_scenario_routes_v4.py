"""Ten registered V4 scenes. Each choice uses the same resolver and public actions."""

import pytest
from game import catalog, world
from game.world_templates import scene_line, reply, case_line, ending_detail
from tests.test_world_v4 import Play, D, Q


def reject(g, kind, **args):
    rev = g.s["revision"]
    with pytest.raises(ValueError):
        g.do(kind, **args)
    assert g.s["revision"] == rev


def test_sc01_fiscal_routes_and_preconditions():
    outcomes = []
    for plan in ("A", "B", "C"):
        g = Play()
        reject(g, "propose", plan=plan)
        g.go("L03").do("permit", project="P02").do("permit", project="P03").wait(2 * D)
        g.do("propose", plan=plan).wait(180).do("offer", offer="OF-1", choice="accept")
        outcomes.append(
            tuple(
                (i, p.get("allocation", 0), p["phase"])
                for i, p in g.d["projects"].items()
            )
        )
        assert (
            g.d["fiscal"]["reserved"] <= 2000 * catalog.WAN
            and sum(g.d["fiscal"]["groups"].values()) <= 12
        )
    assert len(set(outcomes)) == 3


def test_sc02_report_routes_and_absent_sources():
    g = Play()
    reject(g, "revise")
    g.do("compare").wait(30)
    assert g.d["docs"]["D01-index"]["source"] == "本人"
    h = Play()
    h.do("delegate").wait(120)
    assert h.d["docs"]["D01-index"]["source"] == catalog.PEOPLE["N11"]["name"]
    j = Play()
    j.do("reply", mode="conditional")
    assert j.d["flags"]["reply"] == "conditional" and "D01-detail" not in j.d["docs"]


def test_sc03_three_distinct_speech_obligations():
    for mode in ("limited", "assure", "decline"):
        g = Play()
        reject(g, "speak", mode=mode)
        g.do("invite", choice="yes").go("L04").do("speak", mode=mode).wait(200)
        pr = list(g.d["promises"].values())
        assert (len(pr) == 1) == (mode == "decline")
        if mode != "decline":
            assert pr[-1]["type"] == mode
        if mode == "assure":
            assert any(x.startswith("SPEECH-reliance-") for x in g.d["docs"])
        assert g.d["fiscal"]["paid"] == 0


def test_sc04_three_distinct_care_costs_and_expired_training():
    scheduled = []
    for mode in ("cover", "share", "decline"):
        g = Play()
        g.go("L07").do("family_plan", mode=mode).wait(40)
        scheduled.append(
            sum(
                t["payload"]["duration"]
                for t in g.s["queue"]
                if t["kind"] == "care_visit"
            )
        )
        g.wait(7 * D)
        reject(g, "family_plan", mode=mode)
    assert scheduled == [180, 60, 0]


def test_sc05_local_and_independent_evidence_and_refused_interpretation():
    photo = next(
        g
        for i in range(100)
        if (g := Play(seed=str(i))).d["variant"]["id"] == "V4-TV04"
    )
    photo.go("L02").do("observe").wait(45).do("evidence").wait(190)
    material = {doc["id"]: doc for doc in world.project(photo.d)["documents"]}
    assert material["P01-photo-east"]["source"] != material["D01-detail"]["source"]
    assert (
        len(
            {
                material[key]["scope"]
                for key in ("P01-photo-east", "D01-detail", "OBS-site")
            }
        )
        == 3
    )
    assert all(
        material[key]["date"] and material[key]["refs"]
        for key in ("P01-photo-east", "D01-r1", "D01-detail", "OBS-site")
    )
    assert (
        "背面" in material["D01-detail"]["body"]
        and not photo.d["investigation"]["findings"]
    )
    g = Play()
    reject(g, "observe")
    g.go("L02").do("observe").wait(45)
    assert g.d["docs"]["OBS-site"]["kind"] == "本人观察"
    h = Play()
    h.do("evidence").wait(180)
    assert h.d["docs"]["D01-detail"]["source"] == catalog.PEOPLE["N18"]["name"]
    j = Play()
    j.do("passage", step="inspect").wait(180)
    assert j.d["passage"]["checks"] and not j.d["passage"]["opened"]


def test_sc06_and_sc10_three_distinct_eligible_office_results_and_constraints():
    results = []
    for mode in ("self", "peer", "observe"):
        g = Play()
        reject(g, "nominate", mode="self")
        g.do("start_channel").wait(100).do("delegate").wait(100).do("revise").wait(35)
        if mode != "observe":
            g.go("L03").do("cooperate").wait(60).go("L01")
        g.wait(4 * Q - g.s["minute"])
        assert g.d["career"]["vacancy"] == "POS-C1"
        if mode != "observe":
            g.do("nominate", mode=mode)
        else:
            g.do("nominate", mode="wait")
        g.wait(10 * D)
        results.append(g.d["career"]["positions"]["POS-C1"])
        assert g.d["docs"]["D01-r1"]["version"] == "r1"
    assert results == ["player", "N03", "N07"]


def test_sc07_mentor_routes_correct_dated_information_and_interest():
    g = Play()
    reject(g, "mentor", who="N12", mode="ask")
    g.do("invite", choice="yes").go("L04").do("mentor", who="N12", mode="ask").wait(20)
    initial = g.d["docs"]["advice-N12ask"]["body"]
    assert "上次" in initial
    g.do("mentor", who="N12", mode="limited").wait(180)
    assert any(v["from"] == "N12" for v in g.d["favours"].values())
    g.wait(4 * D)
    g.do("mentor", who="N12", mode="verify").wait(240)
    assert g.d["docs"]["D12-check-N12"]["body"] != initial
    g.go("L08").do("mentor", who="N13", mode="ask").wait(30)
    assert "哪一任" in g.d["docs"]["advice-N13ask"]["body"]


def test_sc08_same_note_is_private_read_or_preserved_by_different_actions():
    text = "我推测这次数字采用了不同范围。"
    for route in ("private", "reader", "copy"):
        g = Play()
        g.do("write_note", text=text)
        if route == "private":
            g.go("L02").wait(200)
            assert not g.d["notebook"]["copies"] and "K13" not in g.d["cases"]
        elif route == "reader":
            g.do("leave_note").go("L02").wait(200)
            assert g.d["cases"]["K13"]["status"] == "contested" and text not in str(
                world.project(g.d)
            )
            reject(g, "copy_note")
        else:
            g.do("copy_note").wait(180).do("destroy_note").do(
                "confirm_note", choice="yes"
            )
            assert (
                g.d["notebook"]["copies"][0]["holder"] == "N19"
                and not g.d["investigation"]["findings"]
            )


def test_sc09_three_quarter_old_scope_record_and_three_conditional_review_outcomes():
    outcomes = set()
    for mode in ("file", "witness", "scope"):
        g = Play()
        reject(g, "legacy_review", mode=mode)
        for step in ("inspect", "approve"):
            g.do("passage", step=step).wait(200)
        g.go("L02").do("passage", step="open").wait(60)
        g.wait(Q)
        if mode == "file":
            g.do("service_passage").wait(125).go("L01")
            g.do(
                "write_sourced_note",
                document="P01-opening",
                classification="引用文件",
                text="交接单只涉及西段。",
            )
            g.do("copy_note").wait(180).do("destroy_note").do(
                "confirm_note", choice="yes"
            )
        if g.d["location"] != "L01":
            g.go("L01")
        g.wait(2 * Q)
        assert g.d["legacy_review"]["claim"] and not g.d["investigation"]["findings"]
        if mode != "file":
            reject(g, "legacy_review", mode="file")
            assert len(g.d["legacy_review"]["acquired"]) == 1
        else:
            assert (
                g.d["notebook"]["copies"][0]["receipt"]
                in g.d["legacy_review"]["acquired"]
            )
            assert "副本" in g.d["cases"]["K14"]["history"][-1]["text"]
        g.do("legacy_review", mode=mode).wait(240)
        outcomes.add(g.d["legacy_review"]["status"])
        assert g.d["passage"]["opened"] and not g.d["investigation"]["findings"]
    assert outcomes == {"已有维护证据归档", "开放范围获佐证", "补件整改"}


def test_minimum_offline_templates_are_registered_and_conditioned():
    g = Play()
    for key, npc in catalog.PEOPLE.items():
        claim = g.d["actors"][key]["beliefs"]["genesis/" + key]
        lines = [
            reply(claim, "normal"),
            reply(claim, "source"),
            reply(claim, "blocked", npc["plan"]),
        ]
        assert all(claim in t for t in lines) and len(set(lines)) == 3
        with pytest.raises(ValueError):
            reply(claim, "blocked")
    for place in catalog.LOCATIONS:
        assert (
            len(
                {
                    scene_line(place, mode)
                    for mode in ("enter", "leave", "wait", "denied")
                }
            )
            == 4
        )
    for key, info in catalog.CASES.items():
        lines = [
            case_line(key, state, "收件人签收可出示的新材料。")
            for state in ("signal", "active", "contested", "dormant", "resolved")
        ]
        assert (
            len(
                set(
                    lines
                    + [case_line(key, "active", "收件人签收可出示的新材料。", True)]
                )
            )
            == 6
        )
        assert all(info["name"] in t for t in lines)
    for key, ending in catalog.ENDINGS.items():
        bare, refs = ending_detail(key, ending["name"], [], 2)
        assert "2 项" in bare and not refs
        source = {
            "id": "POST-S01",
            "kind": "文件声称",
            "title": "实际收件回执",
            "refs": ["record-1"],
        }
        other, refs = ending_detail(key, ending["name"], [source], 0)
        assert other != bare and refs == ["record-1"]
