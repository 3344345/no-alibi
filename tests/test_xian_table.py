"""The eyewitness chair trades a political guarantee for later, personal testimony."""

import pytest

from game.chronicle import ChronicleStore, Command
from game.chronicle_serial import SERIAL_EDITION
from game.store import GameStore
from game.witness_xian_chairs import COPPER, DINNER, DRIVER, INK, KEY, LANDING


def walk(store, view, *keys):
    for key in keys:
        view = store.choose(view["id"], Command(
            revision=view["revision"], command_id=f"table-{view['revision']}", choice=key
        ))
    return view


@pytest.mark.parametrize("edition", [None, SERIAL_EDITION])
@pytest.mark.parametrize("first,second,witness,testimony,after,other", [
    pytest.param("nanking", "chair_x", LANDING, "call_runway", INK, "call_driver", id="runway"),
    pytest.param("civil", "chair_n", DRIVER, "call_driver", KEY, "call_ledger", id="driver"),
    pytest.param("xian", "chair_c", DINNER, "call_ledger", COPPER, "call_runway", id="ledger"),
])
def test_witnesses_return_at_supper_in_court_and_ten_years_later(
    tmp_path, edition, first, second, witness, testimony, after, other
):
    store = ChronicleStore(GameStore(tmp_path / "original.db"))
    if edition:
        view = store.create("茶凉了", "witness", edition=edition)
    else:
        view = store.create("茶凉了", "witness", "witness_zhang_xueliang", "third_chair")
    view = walk(store, view, first, "offer_word", second, "offer_word")
    assert view["scene"]["id"] == "xian_supper"
    assert witness in view["marks"]
    assert len(view["scene"]["callbacks"]) == 2
    copy = ChronicleStore(GameStore(tmp_path / "restored.db"))
    assert copy.restore(store.export(view["id"])) == view
    view = walk(copy, view, "say", "pay")
    assert [c["id"] for c in view["scene"]["choices"]] == ["trial"]
    view = walk(copy, view, "trial")
    available = {c["id"] for c in view["scene"]["choices"]}
    assert testimony in available and other not in available
    view = walk(copy, view, testimony, "sleeves")
    assert view["scene"]["id"] == "xian_future_trial"
    assert view["scene"]["callbacks"][0]["origin"] == next(
        i for i, entry in enumerate(view["journal"]) if entry["choice"] == testimony
    )
    assert after in view["marks"]
    assert copy.view(view["id"]) == view
