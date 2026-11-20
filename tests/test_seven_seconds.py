"""Play all six endings, including conditional endings on opposite sides of the sale."""

import pytest

from game.chronicle import Branch, ChronicleStore, Command
from game.store import GameStore
from game.witness_seven_seconds import BRASS, FULL, PROMISE


def walk(store, view, sequence):
    for choice in sequence.split():
        view = store.choose(view["id"], Command(revision=view["revision"],
            command_id=f"tape-{view['revision']}", choice=choice))
    return view


def opening(store):
    return store.create("旧礼堂", "witness", "witness_deng_xiaoping", opening_choice="seven_seconds")


@pytest.mark.parametrize("sequence,ending", [
    ("follow_chair carry_chair cut_full take_blame yard chair_ticket end_doors", "散场的门不落闩"),
    ("follow_mother keep_key let_listen use_silence teacher_key one_student end_home", "两个人的一课"),
    ("follow_chair keep_out ask_live ask_name shop quiet_hour end_duet", "没收进去的掌声"),
    ("follow_mother ask_daughter cut_ad let_crash offer_air hire_truck bolt_name end_metal", "少半个字的合影"),
    ("follow_chair keep_out let_listen invite_guest offer_air yard take_home end_window", "碗沿上的片尾"),
    ("follow_mother keep_key cut_full give_rebuttal ask_name teacher_key take_hand red_price end_wake", "天亮以前的台呼"),
])
def test_complete_performances(tmp_path, sequence, ending):
    store = ChronicleStore(GameStore(tmp_path / "career.db"))
    view = walk(store, opening(store), sequence)
    assert view["finished"] and view["chapter_count"] == 1
    assert view["marks"][-1] == "散场结局 · " + ending
    imported = ChronicleStore(GameStore(tmp_path / "tour.db"))
    assert imported.restore(store.export(view["id"])) == view


def test_recutting_tape_changes_the_truck_booking_and_the_last_photo(tmp_path):
    store = ChronicleStore(GameStore(tmp_path / "career.db"))
    mix = walk(store, opening(store), "follow_chair carry_chair")
    branch = store.fork(mix["id"], Branch(revision=mix["revision"]))
    full = walk(store, mix, "cut_full take_blame")
    sale = walk(store, branch, "cut_ad honor_sale")
    assert FULL in full["marks"] and PROMISE not in full["marks"]
    assert all(c["id"] != "hire_truck" for c in full["scene"]["choices"])
    assert PROMISE in sale["marks"] and FULL not in sale["marks"]
    end = walk(store, sale, "hire_truck bolt_name")
    assert BRASS in end["marks"]
    assert end["journal"][next(c for c in end["scene"]["callbacks"] if "铜牌" in c["body"])["origin"]]["choice"] == "bolt_name"
