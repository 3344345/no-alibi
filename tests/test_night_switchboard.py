"""New callbacks coexist with archived shortcuts in both versions of the night line."""

import pytest

from game.chronicle import ChronicleStore, Command
from game.store import GameStore
from game.witness_switchboard import BAKER, BELL, CONDUCTOR, NAME, PAPER, SLICE


def play(store, view, route):
    for key in route.split():
        view = store.choose(view["id"], Command(
            revision=view["revision"], command_id=f"patch-{view['revision']}", choice=key,
        ))
    return view


@pytest.mark.parametrize(("path", "guest", "loss", "meeting", "mark", "last"), [
    ("public", "baker", False, "pin_paper", PAPER, "那个歪字"),
    ("private", "conductor", False, "home_name", NAME, "家里的叫法"),
    ("private", "baker", True, "cut_slice", SLICE, "缺了角"),
    ("public", "conductor", True, "pull_bell", BELL, "隔条过道"),
])
def test_broadcast_callbacks_survive_export_and_1992(tmp_path, path, guest, loss, meeting, mark, last):
    store = ChronicleStore(GameStore(tmp_path / "live.db"))
    view = store.create("夜班", "witness", "witness_deng_xiaoping", opening_choice="night_line")
    view = play(store, view, f"patch_{path}_{guest}")
    expected_route = "night_coins" if path == "public" else "night_listen"
    assert view["scene"]["id"] == expected_route
    callback = BAKER if guest == "baker" else CONDUCTOR
    assert callback in view["marks"]
    view = play(store, view, "airtime" if path == "public" else "laugh")
    assert ("奶油字" if guest == "baker" else "家乡口音") in view["scene"]["body"]
    view = play(store, view, "sheet date kin father hand voice letters together closed caller repeat")
    view = play(store, view, "martial keep record name visit" if loss else "morning hold ride")
    keys = {c["id"] for c in view["scene"]["choices"]}
    assert ("visit_bakery" in keys, "ride_with_feng" in keys) == (guest == "baker", guest == "conductor")
    view = play(store, view, "visit_bakery" if guest == "baker" else "ride_with_feng")
    next_store = ChronicleStore(GameStore(tmp_path / "restore.db"))
    assert next_store.restore(store.export(view["id"])) == view
    view = play(next_store, view, meeting)
    assert last in view["journal"][-1]["result"]
    assert mark in view["marks"]
    if loss:
        assert view["scene"]["id"] == "night_loss_autumn_stool"
        view = play(next_store, view, "keep along")
    else:
        view = play(next_store, view, "count names away coach" if guest == "baker" else "year names away coach")
    assert view["scene"]["id"] in {"night_coach", "night_loss_winter_counter"}
    assert {PAPER:"灯罩还来了", SLICE:"小碟", BELL:"托住铃口", NAME:"坐在最后面"}[mark] in view["scene"]["body"]


def test_plain_shortcut_and_serial_edition_keep_distinct_callbacks(tmp_path):
    store = ChronicleStore(GameStore(tmp_path / "routes.db"))
    direct = store.create("老接法", "witness", "witness_deng_xiaoping", opening_choice="night_line")
    direct = play(store, direct, "public airtime sheet date kin father hand voice letters together closed caller repeat morning hold ride")
    assert {"visit_bakery", "ride_with_feng"}.isdisjoint(c["id"] for c in direct["scene"]["choices"])
    standard = store.witness.scene_maps[store.witness.indices["witness_deng_xiaoping"]]
    serial = store.serial.scene_maps[store.serial.indices["witness_deng_xiaoping"]]
    for key in ("night_switchboard", "night_platform", "night_loss_autumn_glass", "night_patch_bell", "night_loss_patch_bakery"):
        assert [(c.id, c.next, c.marks, c.requires) for c in standard[key].choices] == [
            (c.id, c.next, c.marks, c.requires) for c in serial[key].choices
        ]
