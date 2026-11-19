"""The county and both chronicles can coexist, including saves from the first chronicle release."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from api.routes import make_app
from game.balance import canonical
from game.chronicle import Book, Branch, ChronicleStore, Command
from game.engine import GameError
from game.store import GameStore
from main import restore_archive
from tests.test_chronicle import sample


@pytest.fixture
def published(monkeypatch):
    witness = deepcopy(sample())
    witness[0].update(id="early", year="1919", role="早期人物")
    witness[1].update(id="later", year="1989", role="后期人物")
    monkeypatch.setattr("game.chronicle.load_witness", lambda: Book(witness, "witness"))
    monkeypatch.setattr("game.chronicle.load_book", lambda: Book(sample()))


def test_migrates_prior_two_column_sqlite_and_original_json_without_claiming_witness_id(
    tmp_path, published
):
    db = GameStore(tmp_path / "release.db")
    old_id = "0" * 32
    payload = dict(format="juzhongshi-chronicle/1", id=old_id, name="家书", commands=[])
    payload["checksum"] = hashlib.sha256(canonical([payload, []]).encode()).hexdigest()
    with db._db(write=True) as conn:
        conn.execute(
            "CREATE TABLE chronicle_careers (id TEXT PRIMARY KEY, name TEXT NOT NULL)"
        )
        conn.execute("INSERT INTO chronicle_careers VALUES(?,?)", (old_id, "家书"))
    chron = ChronicleStore(db)
    original = chron.view(old_id)
    assert original["campaign"] == "family" and original["start_chapter"] == "a"
    upgraded = chron.export(old_id)
    assert upgraded["format"] == "juzhongshi-chronicle/3" and upgraded["chapters"] == [
        "a",
        "b",
    ]
    assert upgraded["commands"] == payload["commands"]
    assert chron.restore(payload) == original
    assert chron.catalogue("witness")["careers"] == []
    # A valid witness archive with the same file identity cannot replace a family's file.
    other = ChronicleStore(GameStore(tmp_path / "elsewhere.db"))
    with other.database._db(write=True) as conn:
        conn.execute(
            "INSERT INTO chronicle_careers(id,name,campaign,start_chapter) VALUES(?,?,?,?)",
            (old_id, "家书", "witness", "later"),
        )
    with pytest.raises(GameError, match="保留"):
        chron.restore(other.export(old_id))
    assert chron.view(old_id) == original
    assert chron.catalogue()["careers"][0]["id"] == old_id


def test_character_start_api_lists_fork_cli_export_and_tampering(tmp_path, published):
    db = GameStore(tmp_path / "combined.db")
    (tmp_path / "index.html").write_text("fixture")
    client = TestClient(
        make_app(db, "token", tmp_path, 45711),
        base_url="http://127.0.0.1:45711",
        headers={"Authorization": "Bearer token"},
    )
    base = "/api/chronicle"
    family = client.post(base, json={"name": "同名"}).json()
    first = client.post(base, json={"name": "同名", "campaign": "witness"}).json()
    assert first["start_chapter"] == "early"
    selected = client.post(
        base, json={"name": "同名", "campaign": "witness", "start_chapter": "later"}
    ).json()
    uid = selected["id"]
    assert selected["start_chapter"] == selected["chapter"]["id"] == "later"
    assert (
        selected["chapter"]["role"] == "后期人物"
        and selected["marks"] == selected["journal"] == []
    )
    assert [s["id"] for s in client.get(base).json()["careers"]] == [family["id"]]
    assert {
        s["id"]
        for s in client.get(base, params={"campaign": "witness"}).json()["careers"]
    } == {first["id"], uid}
    assert client.get(base, params={"campaign": "wrong"}).status_code == 422
    for cid, campaign in (("later", "family"), ("bad", "witness")):
        assert (
            client.post(
                base,
                json={"name": "坏入口", "campaign": campaign, "start_chapter": cid},
            ).status_code
            == 422
        )
    path = base + "/" + uid
    assert (
        client.post(
            path + "/choices",
            json={"revision": 0, "command_id": "locked", "choice": "file"},
        ).status_code
        == 422
    )
    completed = client.post(
        path + "/choices", json={"revision": 0, "command_id": "go", "choice": "ask"}
    ).json()
    assert completed["finished"] and completed["revision"] == 1
    archive = client.get(path + "/export").json()
    assert (archive["format"], archive["campaign"], archive["start_chapter"]) == (
        "juzhongshi-chronicle/3",
        "witness",
        "later",
    )
    for attack in (
        dict(campaign="family"),
        dict(start_chapter="early"),
        dict(format="juzhongshi-chronicle/1"),
    ):
        assert (
            client.post(base + "/import", json={**archive, **attack}).status_code == 422
        )
    assert client.get(path).json() == completed
    branch = client.post(path + "/fork", json={"revision": 0}).json()
    assert branch["id"] != uid and branch["campaign"] == "witness"
    assert (
        branch["start_chapter"] == branch["chapter"]["id"] == "later"
        and not branch["journal"]
    )
    file = tmp_path / "导出.json"
    file.write_text(json.dumps(archive, ensure_ascii=False))
    new = GameStore(tmp_path / "imported.db")
    assert restore_archive(new, file) == completed
    assert ChronicleStore(new).catalogue()["careers"] == []


def test_concurrent_cross_campaign_choices_share_neither_receipts_nor_progress(
    tmp_path, published
):
    store = ChronicleStore(GameStore(tmp_path / "same.db"))
    family = store.create("家书")
    witness = store.create("人物", "witness")
    req = Command(revision=0, command_id="one", choice="keep")
    ids = [family["id"], witness["id"]] * 5
    with ThreadPoolExecutor(max_workers=5) as pool:
        replies = list(pool.map(lambda uid: store.choose(uid, req), ids))
    for i, reply in enumerate(replies):
        assert reply["id"] == ids[i] and reply["revision"] == 1
        assert reply["campaign"] == ("family" if ids[i] == family["id"] else "witness")
    assert store.export(family["id"])["format"] == "juzhongshi-chronicle/3"
    assert store.export(witness["id"])["format"] == "juzhongshi-chronicle/3"
    branch = store.fork(witness["id"], Branch(revision=1))
    assert branch["journal"] == replies[1]["journal"]
    assert branch["campaign"] == "witness" and branch["start_chapter"] == "early"


def test_every_published_witness_can_begin_directly_and_travel_in_calendar_order(
    tmp_path,
):
    from game.chronicle import load_witness

    book = load_witness()
    years = [int(ch.year[:4]) for ch in book.chapters]
    assert years == sorted(years)
    assert {"witness_liu_qingshan", "witness_xiaogang"} <= {
        ch.id for ch in book.chapters
    }
    assert any(
        "邓小平" in ch.role and ch.year.startswith("1989") for ch in book.chapters
    )
    store = ChronicleStore(GameStore(tmp_path / "published.db"))
    for i, ch in enumerate(book.chapters):
        # Every credential-gated option in this person's chapter is attainable
        # without having acquired any object in an earlier life.
        Book([ch.model_dump()], "witness")
        view = store.create(ch.role, "witness", ch.id)
        assert (
            view["chapter"]["id"] == ch.id and view["chapter"]["history"] == ch.history
        )
        assert view["start_chapter"] == ch.id and view["marks"] == view["journal"] == []
        for step in range(len(ch.scenes)):
            if view["finished"] or view["chapter"]["id"] != ch.id:
                break
            old = view
            assert old["scene"]["choices"]
            req = Command(
                revision=old["revision"],
                command_id=str(step),
                choice=old["scene"]["choices"][0]["id"],
            )
            view = store.choose(old["id"], req)
            assert view["journal"][-1]["role"] == ch.role
        if i + 1 < len(book.chapters):
            assert (
                not view["finished"]
                and view["chapter"]["id"] == book.chapters[i + 1].id
            )
        else:
            assert view["finished"]
        file = store.export(view["id"])
        assert file["start_chapter"] == ch.id
        assert store.restore(file) == view
    assert store.catalogue("family")["careers"] == []
