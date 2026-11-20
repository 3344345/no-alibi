"""Play the cinema arc through county actions, real money, calendar and storage."""
import pytest
from game.engine import GameError
from game.store import GameStore
from game.world_aftershow import FEE, SCENES
from tests.test_world_v4 import Play


def take(p, key):
    from game.world_aftershow import options
    chosen, = [o for o in options(p.d) if o["args"]["choice"] == key]
    p.do("aftershow", **chosen["args"])
    if due := p.d["aftershow"].get("due"):
        p.wait(due - p.s["minute"])


@pytest.mark.parametrize("route, echo, ending, charged", [
    ("mother borrow_ticket take_fee paid_listen show_wages refund_queue repay", "凉水", "returned", False),
    ("daughter stay_booth take_fee paid_quiet show_empty lift_chair keep", "半个巴掌", "kept", True),
    ("daughter fetch_mother leave_ticket stay_guest seat_with_mother show_girl give_mother close_reel", "又是她家", "home", False),
    ("mother borrow_ticket stay_guest seat_with_daughter show_girl give_worker screen_workers", "开", "open", False),
    ("daughter stay_booth stay_guest seat_with_mother show_wages workers_first screen_workers", "酥糖", "open", False),
    ("mother leave_ticket take_fee paid_listen show_empty hang_name repay", "锃亮", "returned", False),
])
def test_theatre_money_and_screening_change_the_reunion(route, echo, ending, charged):
    from game.world_aftershow import project
    p = Play()
    take(p, "attend")
    for key in route.split()[:-1]:
        before = p.d["family"]["savings"]
        take(p,key)
        if key == "take_fee":
            assert p.d["family"]["savings"] == before + FEE
            assert "CIN-take_fee" in p.d["docs"]
    assert p.s["minute"] >= 30 * 1440 and echo in project(p.d)["body"]
    before = p.d["family"]["savings"]
    take(p,route.split()[-1])
    after = p.d["family"]["savings"]
    assert before - after == (FEE if ending == "returned" else 0)
    assert ("CIN-take_fee" in p.d["docs"] and "CIN-repay" not in p.d["docs"]) == charged
    assert project(p.d)["stage"] == "ending" and project(p.d)["title"] == SCENES[ending].title
    assert p.d["docs"]["CIN-ending"]["refs"]
    p.do("night_bus", scene="call", choice="arrange")
    assert p.d["night_bus"]["node"] == "curb"


def test_restore_fork_and_duplicate_fees(tmp_path):
    s = GameStore(tmp_path/"first.sqlite")
    v = s.create()
    ident = v["world_id"]
    def do(key):
        nonlocal v
        if v["aftershow"]["due"] is not None:
            v = s.execute(ident,"wait"+str(v["revision"]),v["revision"],"advance",
                          {"minutes":v["aftershow"]["due"]-v["minute"]})
        cmd = "pick"+str(v["revision"])
        args={"scene":v["aftershow"]["node"],"choice":key}
        v = s.execute(ident,cmd,v["revision"],"aftershow",args)
        assert s.execute(ident,cmd,v["revision"]-1,"aftershow",args)==v
    for k in "attend daughter stay_booth take_fee paid_listen".split():
        do(k)
    other=GameStore(tmp_path/"other.sqlite")
    assert other.restore(s.export(ident))["aftershow"] == v["aftershow"]
    fork=s.fork(ident,v["revision"])
    do("show_girl")
    other_view=s.execute(fork["world_id"],"fork-film",fork["revision"],"aftershow",{"scene":"spool","choice":"show_empty"})
    assert v["aftershow"]["node"]=="family" and other_view["aftershow"]["node"]=="chair"
    with pytest.raises(GameError):
        s.execute(ident,"skip",v["revision"],"aftershow",{"scene":"month","choice":"keep"})
