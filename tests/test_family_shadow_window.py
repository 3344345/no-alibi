import pytest

from game.chronicle import Branch, ChronicleStore, Command
from game.family_shadow_window import BRIDE, PART, TOGETHER, play
from game.store import GameStore


def move(store, view, key):
    assert key in {ch["id"] for ch in view["scene"]["choices"]}
    return store.choose(view["id"], Command(revision=view["revision"], command_id=f"c-{view['revision']}", choice=key))


def walk(store, view, keys):
    for key in keys.split():
        view = move(store, view, key)
    return view


@pytest.mark.parametrize(("sequence", "mark", "payoff"), [
    ("face_ask_friend face_owe face_pull face_take_coins face_sell_blank face_come_again", PART, "半只猴子"),
    ("face_ask_friend face_owe face_double face_kid face_trade_chest face_bench_rest", TOGETHER, "拓样"),
    ("face_ask_bride face_give_wing face_walk face_bride_voice face_wait face_wedding_gift face_draw_blank", BRIDE, "痣的位置"),
])
def test_booth_tradeoffs_return_in_the_later_kitchen(tmp_path, sequence, mark, payoff):
    store = ChronicleStore(GameStore(tmp_path / "original"))
    view = store.create("喜棚", "family", opening_choice="borrow_a_face")
    assert view["scene"]["id"] == "face_box"
    view = walk(store, view, sequence)
    assert view["scene"]["id"] == "face_letter" and payoff in view["scene"]["body"]
    assert set(view["marks"]) & {BRIDE, TOGETHER, PART} == {mark}
    fresh = ChronicleStore(GameStore(tmp_path / "fresh"))
    assert fresh.restore(store.export(view["id"])) == view
    view = move(fresh, view, "face_visit_end")
    while view["chapter"]["id"] != "nantao_refuge":
        view = move(fresh, view, view["scene"]["choices"][0]["id"])
    callback = [row for row in view["scene"]["callbacks"] if mark in view["journal"][row["origin"]]["marks"]]
    assert len(callback) == 1


def test_the_bride_can_only_speak_if_she_was_invited_backstage(tmp_path):
    store = ChronicleStore(GameStore(tmp_path / "branched"))
    start = store.create("戏窗", "family", opening_choice="borrow_a_face")
    copy = store.fork(start["id"], Branch(revision=start["revision"]))
    for view, route, invited in [
        (start, "face_ask_friend face_owe face_walk", False),
        (copy, "face_ask_bride face_give_wing face_walk", True),
    ]:
        door = walk(store, view, route)
        assert ("face_bride_voice" in {c["id"] for c in door["scene"]["choices"]}) == invited
        settlement = move(store, door, "face_finish_silent")
        assert ("face_wedding_gift" in {c["id"] for c in settlement["scene"]["choices"]}) == invited
    assert len({node["id"] for node in play()}) == len(play())
