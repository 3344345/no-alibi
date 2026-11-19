from game import balance, engine
from game import world
from tests.test_world_v4 import Play


def test_only_selected_entry_disclosed_to_present_mentor():
    play = (
        Play()
        .do("write_note", text="我猜两份统计范围不同")
        .do("write_note", text="仅供自己看的安排")
    )
    play.go("L08")
    view = play.s["domain"]
    before = set(view["actors"]["N13"]["beliefs"])
    chosen = view["notebook"]["entries"][0]["ref"]
    play.do("show_entry", mentor="N13", entry_ref=chosen)
    d = play.d
    new = set(d["actors"]["N13"]["beliefs"]) - before
    assert len(new) == 1
    text = d["actors"]["N13"]["beliefs"][next(iter(new))]
    assert "我猜" in text and "仅供自己" not in text
    assert not any("我猜" in word for word in d["actors"]["N12"]["beliefs"].values())
    seen = d["disclosures"][-1]
    assert seen["entry_ref"] == chosen and seen["received"] in new


def test_spouse_requires_continuous_access_to_read_notebook():
    text = "这一条只记了自己对旧排期的猜测。"
    g = Play().do("write_note", text=text).go("L07")
    assert world.present(g.d, "N14", "L07")
    g.wait(100)
    assert text not in g.d["actors"]["N14"]["beliefs"].values()
    g.do("leave_note").wait(60)
    notices = [e for e in g.log if e["actor"] == "N14" and e["title"] == "物品被发现"]
    assert len(notices) == 1 and text not in g.d["actors"]["N14"]["beliefs"].values()
    # Take the book back before reading and put it down again. The first
    # discovery must not grant access for the second placement.
    g.do("take_note").do("leave_note").wait(89)
    assert text not in g.d["actors"]["N14"]["beliefs"].values()
    g.wait(1)
    reading = [e for e in g.log if e["actor"] == "N14" and e["title"] == "阅读记录"]
    assert len(reading) == 1 and reading[0]["refs"] != [notices[0]["id"]]
    assert g.d["actors"]["N14"]["beliefs"][reading[0]["id"]] == text


def test_stale_crew_notice_allows_request_and_limits_failure_feedback():
    g = Play().go("L03")
    for key in ("P02", "P03"):
        g.do("permit", project=key)
    g.wait(2880).do("propose", plan="A").wait(180)
    g.do("department_round")
    original = g.d["actors"]["N08"]["belief_topics"]["crew_notice"]
    assert "12 组" in g.d["actors"]["N08"]["beliefs"][original]
    g.do("offer", offer="OF-1", choice="accept")
    assert sum(g.d["fiscal"]["groups"].values()) == 12
    g.wait(45)
    bid = g.d["department_round"]["bids"]["P01"]
    assert bid["applicant"] == "N08" and bid["groups"] > 0 and not bid["waitlist"]
    assert "crew_response" not in g.d["actors"]["N08"]["belief_topics"]
    g.wait(120)
    actor = g.d["actors"]["N08"]
    ref = actor["belief_topics"]["crew_response"]
    assert actor["beliefs"][ref] == "受理申请时，你所报的完整班组时段已无法安排。可在下一窗口重新申请。"
    result = next(e for e in g.log if e["id"] == ref)
    assert result["refs"] == [bid["source"]] and not result["visible"]
    assert not any(result["id"] == e["id"] for e in engine.player_view(g.s)["timeline"])
    assert sum(g.d["fiscal"]["groups"].values()) == 12

    informed = Play().go("L03")
    for key in ("P02", "P03"):
        informed.do("permit", project=key)
    informed.wait(2880).do("propose", plan="A").wait(180)
    informed.do("offer", offer="OF-1", choice="accept").do("department_round").wait(180)
    assert informed.d["department_round"]["bids"]["P01"]["waitlist"]
    assert "crew_response" not in informed.d["actors"]["N08"]["belief_topics"]


def test_safe_seat_skips_accident_and_alert_precedes_exposure():
    wet = next(
        str(i)
        for i in range(100)
        if balance.uniform(str(i), "genesis/window-condition") < 0.22
    )
    dry = next(
        str(i)
        for i in range(100)
        if balance.uniform(str(i), "genesis/window-condition") >= 0.22
    )
    safe = Play(seed=dry).do("window_rest").wait(45)
    assert not safe.d["ended"] and not any(
        "/environment" in e.get("data", {}).get("slot", "") for e in safe.log
    )
    damp = Play(seed=wet)
    source = damp.d["office_window"]["source"]
    alert = next(e for e in engine.player_view(damp.s)["timeline"] if e["id"] == source)
    assert alert["minute"] == 0 and "积水提示牌" in alert["text"]
    damp.do("rest").wait(45)
    assert not any(
        "/environment" in e.get("data", {}).get("slot", "") for e in damp.log
    )
    damp.do("window_rest").wait(45)
    assert any("/environment" in e.get("data", {}).get("slot", "") for e in damp.log)
    assert not damp.d["ended"]
    damp.do("window_service").wait(30)
    assert not damp.d["office_window"]["wet"]


def test_evening_version_question_and_deferral_have_separate_results():
    attempts = [
        {"id": "hold", "kind": "reply", "args": {"mode": "defer"}, "depends_on": []},
        {"id": "ask", "kind": "ask_zhou_attachment", "args": {}, "depends_on": []},
    ]
    g = Play().do("reply", mode="defer").do("batch", attempts=attempts)
    assert [r["status"] for r in g.s["last_action_results"]] == ["unavailable", "accepted"]
    assert g.d["flags"]["zhou_attachment"]["state"] == "待回复"
    g.wait(100)
    assert g.d["flags"]["zhou_attachment"]["state"] == "已约定"
    g.wait(440)
    assert g.d["busy"]["player"]["due"] == g.d["busy"]["N10"]["due"] == 555
    g.wait(15)
    assert g.d["flags"]["zhou_attachment"]["state"] == "已面谈"
    doc = g.d["docs"]["ZHOU-attachment-555"]
    assert doc["source_id"] == "N10" and "r1" in doc["body"] and "无法确认" in doc["body"]
    spoken = next(e for e in g.log if e["id"] == doc["refs"][0])
    received = g.d["actors"]["N10"]["beliefs"][spoken["refs"][-1]]
    assert received in doc["body"] and g.d["variant"]["answer"] not in doc["body"]

    absent = Play().do("ask_zhou_attachment").go("L02").wait(540)
    assert absent.d["flags"]["zhou_attachment"]["state"] == "未能面谈"
    assert not any(key.startswith("ZHOU-attachment") for key in absent.d["docs"])
    late = Play().wait(539).do("ask_zhou_attachment").wait(100)
    assert late.d["flags"]["zhou_attachment"]["state"] == "未能约成"
    assert not any(key.startswith("ZHOU-attachment") for key in late.d["docs"])
