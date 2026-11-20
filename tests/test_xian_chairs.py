"""The two meetings are a limited resource; one side's promise cannot stand for another."""

from collections import deque

import pytest

from game.chronicle import Book, ChronicleStore, Command
from game.store import GameStore
from game.witness_early import CHAPTERS


CHAPTER = next(ch for ch in CHAPTERS if ch["id"] == "witness_zhang_xueliang")


def advance(store, view, keys):
    for key in keys.split():
        view = store.choose(view["id"], Command(revision=view["revision"], command_id=f"pick-{view['revision']}", choice=key))
    return view


@pytest.mark.parametrize(
    ("meet", "offer", "next_room"),
    (
        ("nanking split chair_c alone", "passage", "xian_steamer"),
        ("xian elect chair_n split", "stay", "xian_square"),
        ("civil each chair_x elect", "company", "xian_purse"),
        ("civil pay chair_x elect", None, "xian_bench"),
    ),
)
def test_only_the_two_parties_actually_heard_will_let_zhang_leave(tmp_path, meet, offer, next_room):
    store = ChronicleStore(GameStore(tmp_path / "source.db"))
    view = advance(store, store.create("调停", "witness", CHAPTER["id"]), "third_chair " + meet + " say pay")
    assert view["scene"]["id"] == "xian_bargain"
    offered = {c["id"] for c in view["scene"]["choices"]}
    assert offered == ({"trial", offer} if offer else {"trial"})
    other = ChronicleStore(GameStore(tmp_path / "other.db"))
    saved = other.restore(store.export(view["id"]))
    assert saved == view
    assert advance(other, saved, offer or "trial")["scene"]["id"] == next_room


def test_every_finale_is_attainable_in_ten_separate_rooms():
    book = Book([CHAPTER], "witness")
    queue = deque([("xian_wait", frozenset(), ())])
    visited = set()
    finals = {}
    while queue:
        key, marks, keys = queue.popleft()
        if (key, marks) in visited:
            continue
        visited.add((key, marks))
        for c in book.scene_maps[0][key].choices:
            if not marks.issuperset(c.requires):
                continue
            path = (*keys, c.id)
            if c.next == "END":
                finals[c.id] = path
            else:
                queue.append((c.next, marks.union(c.marks), path))
    assert set(finals) == {"visit", "public", "returner", "lodge", "civil_return", "away", "host"}
    for path in finals.values():
        state = book.beginning()
        book.advance(state, "third_chair")
        for key in path:
            book.advance(state, key)
        assert state["scene"] is None
        assert len({e["scene"] for e in state["journal"][1:]}) == 10
