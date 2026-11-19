"""Regression fixtures use the exact original v2 wire fields and checksum recipe."""

import hashlib
import json
from uuid import uuid4

import pytest

from game.balance import canonical
from game.chronicle import Book, Branch, ChronicleStore, Command, load_witness
from game.chronicle_editions import WITNESS_8, WITNESS_10
from game.engine import GameError
from game.store import GameStore
from tests.test_chronicle import sample


def fingerprint(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def make_old_v2(order, start, stop):
    full = load_witness()
    old = Book([full.chapters[full.indices[c]] for c in order], "witness")
    state = old.beginning(start)
    cmds, hashes = [], []
    while True:
        sc = old.scene_maps[state["chapter"]][state["scene"]]
        c = next(c for c in sc.choices if set(c.requires) <= set(state["marks"]))
        cmds.append(dict(command_id=uuid4().hex, revision=len(cmds), choice=c.id))
        previous = old.chapters[state["chapter"]].id
        event = old.advance(state, c.id)
        hashes.append(old.event_hash(event))
        if previous == stop or state["scene"] is None:
            break
    payload = dict(
        format="juzhongshi-chronicle/2",
        campaign="witness",
        start_chapter=start,
        id=uuid4().hex,
        name="历史发行版",
        commands=cmds,
    )
    payload["checksum"] = fingerprint([payload, hashes])
    return payload, hashes, old.view(payload["id"], payload["name"], state)


@pytest.mark.parametrize(
    "edition", [WITNESS_8, WITNESS_10], ids=["8-chapters", "10-chapters"]
)
def test_legacy_v2_file_and_real_sqlite_find_the_original_release_after_new_insertions(
    tmp_path, edition
):
    # Both careers start at the same chapter. The subsequent log crosses a boundary
    # where the 10-chapter release inserted the Tianjin case into the 8-chapter story.
    start = "witness_zhang_xueliang"
    stop = edition[edition.index(start) + 1]
    archive, hashes, prior = make_old_v2(edition, start, stop)
    catalog = load_witness()
    assert len(catalog.chapters) > len(edition)
    store = ChronicleStore(GameStore(tmp_path / "imported.db"))
    assert store.restore(archive) == prior
    modern = store.export(archive["id"])
    assert modern["format"] == "juzhongshi-chronicle/3" and modern["chapters"] == list(
        edition
    )
    assert store.restore(modern) == prior
    assert store.fork(archive["id"], Branch(revision=0))["chapter_count"] == len(
        edition
    )
    db = GameStore(tmp_path / "legacy.db")
    with db._db(write=True) as conn:
        conn.execute(
            "CREATE TABLE chronicle_careers(id TEXT PRIMARY KEY,name TEXT,campaign TEXT,start_chapter TEXT)"
        )
        conn.execute(
            "CREATE TABLE chronicle_choices(career TEXT,revision INTEGER,command_id TEXT,choice TEXT,event_hash TEXT,PRIMARY KEY(career,revision))"
        )
        conn.execute(
            "INSERT INTO chronicle_careers VALUES(?,?,?,?)",
            (archive["id"], archive["name"], "witness", start),
        )
        conn.executemany(
            "INSERT INTO chronicle_choices VALUES(?,?,?,?,?)",
            [
                (archive["id"], i, c["command_id"], c["choice"], hashes[i])
                for i, c in enumerate(archive["commands"])
            ],
        )
    restarted = ChronicleStore(db)
    assert restarted.view(archive["id"]) == prior
    assert restarted.export(archive["id"]) == modern
    with db._db() as conn:
        assert json.loads(
            conn.execute("SELECT chapter_order FROM chronicle_careers").fetchone()[0]
        ) == list(edition)


def test_new_release_inserts_chapter_but_does_not_retarget_saved_history_or_fork(
    tmp_path,
):
    first, final = sample()
    interlude = {
        **first,
        "id": "inserted",
        "year": "middle",
        "title": "新章",
        "role": "新角色",
    }
    db = GameStore(tmp_path / "active.db")
    old_store = ChronicleStore(db, Book([first, final]))
    initial = old_store.create("代际")
    cmd = Command(revision=0, command_id="first", choice="keep")
    original = old_store.choose(initial["id"], cmd)
    file = old_store.export(original["id"])
    updated = Book([first, interlude, final])
    store = ChronicleStore(db, updated)
    assert store.view(original["id"]) == original == store.choose(original["id"], cmd)
    assert store.export(original["id"]) == file
    entry = store.fork(original["id"], Branch(revision=0))
    assert store.choose(entry["id"], cmd)["chapter"]["id"] == "b"
    new = store.create("新版")
    assert store.choose(new["id"], cmd)["chapter"]["id"] == "inserted"
    other = ChronicleStore(GameStore(tmp_path / "other.db"), updated)
    assert other.restore(file) == original
    for order in (
        ["b", "a"],
        ["a", "a", "b"],
        ["a", "missing", "b"],
        ["a", "inserted", "b"],
    ):
        with pytest.raises(GameError):
            other.restore({**file, "chapters": order})
    assert other.view(original["id"]) == original
