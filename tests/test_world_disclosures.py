from game import balance
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
    damp.do("rest").wait(45)
    assert not any(
        "/environment" in e.get("data", {}).get("slot", "") for e in damp.log
    )
    damp.do("window_rest").wait(45)
    assert any("/environment" in e.get("data", {}).get("slot", "") for e in damp.log)
    assert not damp.d["ended"] and any(
        e["id"] == source and e["minute"] == 0 for e in damp.log
    )
    damp.do("window_service").wait(30)
    assert not damp.d["office_window"]["wet"]
