from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.routes import make_app
from game.chronicle import Book, Branch, ChronicleStore, Command, load_book, load_witness
from game.engine import GameError
from game.store import GameStore


def sample():
    def ch(cid, role, choices):
        return dict(
            id=cid,
            year=cid,
            place="测试地点",
            title=cid,
            role=role,
            intro="引子",
            history="固定史实：" + cid,
            sources=[{"name": "参考资料", "url": "https://example.org/fixture"}],
            scenes=[
                {
                    "id": "entry",
                    "title": "第一页",
                    "body": "可见正文",
                    "choices": choices,
                }
            ],
        )

    return [
        ch(
            "a",
            "甲",
            [
                dict(
                    id="keep",
                    label="保存",
                    result="留下原件",
                    next="END",
                    marks=["原件"],
                    tone="evidence",
                ),
                dict(
                    id="lend",
                    label="借出",
                    result="对方持有原件",
                    next="END",
                    marks=["借据"],
                ),
            ],
        ),
        ch(
            "b",
            "乙",
            [
                dict(
                    id="file",
                    label="核对",
                    result="见到私下批注",
                    next="END",
                    requires=["原件"],
                    marks=["原件", "旁注"],
                    tone="turn",
                ),
                dict(id="ask", label="走访", result="听到后来者的转述", next="END"),
                dict(
                    id="return",
                    label="找回原件",
                    result="收到回信",
                    next="END",
                    requires=["借据"],
                    tone="setback",
                ),
            ],
        ),
    ]


def act(revision, choice, key=None):
    return Command(revision=revision, command_id=key or str(revision), choice=choice)


def store_at(path):
    return ChronicleStore(GameStore(path), Book(sample()))


def test_joined_scene_remembers_first_choice_after_import_and_fork(tmp_path):
    chapters = sample()
    chapters[1]["scenes"][0]["echoes"] = [
        {"mark": "原件", "body": "书架上还放着原件。"},
        {"mark": "借据", "body": "借书人亲自来了。"},
    ]

    def opened(filename):
        return ChronicleStore(GameStore(tmp_path / filename), Book(chapters))

    store = opened("first.db")
    start = store.create("旧书")
    kept = store.choose(start["id"], act(0, "keep"))
    assert kept["scene"]["body"] == "可见正文\n\n书架上还放着原件。"
    restored = opened("second.db").restore(store.export(start["id"]))
    assert restored == kept
    branch = store.fork(start["id"], Branch(revision=0))
    lent = store.choose(branch["id"], act(0, "lend"))
    assert lent["scene"]["body"] == "可见正文\n\n借书人亲自来了。"
    assert store.view(start["id"]) == kept
    chapters[0]["scenes"][0]["echoes"] = [{"mark": "原件", "body": "出现得太早"}]
    with pytest.raises(ValueError, match="后续叙事"):
        Book(chapters)


def test_multiple_careers_handoff_chapter_history_and_hidden_branches(tmp_path):
    store = store_at(tmp_path / "game.db")
    a, b = (store.create("周家"), store.create("周家"))
    assert len(store.catalogue()["careers"]) == 2 and a["id"] != b["id"]
    assert [c["role"] for c in store.catalogue()["chapters"]] == ["甲", "乙"]
    assert set(store.catalogue()["chapters"][0]) == {
        "id",
        "year",
        "place",
        "title",
        "role",
        "intro",
        "history",
        "sources",
    }
    assert a["scene"]["choices"] == [
        {"id": "keep", "label": "保存"},
        {"id": "lend", "label": "借出"},
    ]
    assert all(k not in str(a) for k in ("私下批注", "留下原件", "借据", "tone"))
    left = store.choose(a["id"], act(0, "keep"))
    right = store.choose(b["id"], act(0, "lend"))
    assert left["chapter"] == right["chapter"]
    assert [c["id"] for c in left["scene"]["choices"]] == ["file", "ask"]
    assert [c["id"] for c in right["scene"]["choices"]] == ["ask", "return"]
    assert (
        left["journal"][0]["role"] == "甲" and left["journal"][0]["tone"] == "evidence"
    )
    assert left["journal"][0]["marks"] == ["原件"]
    with pytest.raises(GameError, match="可用"):
        store.choose(b["id"], act(1, "file"))
    assert store.view(b["id"]) == right
    final = store.choose(a["id"], act(1, "file"))
    assert (
        final["finished"]
        and final["scene"] is None
        and final["chapter"] == left["chapter"]
    )
    assert final["marks"] == ["原件", "旁注"] and final["journal"][-1]["marks"] == [
        "旁注"
    ]
    assert final["journal"][-1]["tone"] == "turn"
    assert store_at(tmp_path / "game.db").view(a["id"]) == final
    assert store.choose(a["id"], act(0, "keep")) == left
    with pytest.raises(GameError, match="写完"):
        store.choose(a["id"], act(2, "file"))


def test_concurrent_choices_and_exact_historical_receipts(tmp_path):
    store = store_at(tmp_path / "game.db")
    cid = store.create("测试")["id"]

    def submit(cmd):
        try:
            return store.choose(cid, cmd)
        except GameError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(submit, [act(0, "keep", "same")] * 4))
        assert receipts == [receipts[0]] * 4 and receipts[0]["revision"] == 1
        outcomes = list(pool.map(submit, [act(1, "file", "one"), act(1, "ask", "two")]))
    assert outcomes.count("revision_conflict") == 1
    assert submit(act(0, "lend", "same")) == "idempotency_conflict"
    assert store.view(cid)["revision"] == 2


def test_archive_replay_checks_conflicts_tampering_and_rolls_back_full_import(tmp_path):
    origin = store_at(tmp_path / "original.db")
    cid = origin.create("存档")["id"]
    empty = origin.export(cid)
    first = origin.choose(cid, act(0, "keep"))
    partial = origin.export(cid)
    final = origin.choose(cid, act(1, "file"))
    full = origin.export(cid)
    assert "收到回信" not in str(full)
    db = GameStore(tmp_path / "restored.db")
    restored = ChronicleStore(db, Book(sample()))
    assert restored.restore(partial) == first
    with db._db(write=True) as con:
        con.execute("""CREATE TRIGGER fixture_failure BEFORE INSERT ON chronicle_choices
            WHEN NEW.revision=1 BEGIN SELECT RAISE(ABORT,'write failure'); END""")
    with pytest.raises(sqlite3.DatabaseError, match="write failure"):
        restored.restore(full)
    assert restored.view(cid) == first
    with db._db(write=True) as con:
        con.execute("DROP TRIGGER fixture_failure")
    assert restored.restore(full) == final == restored.restore(full)
    assert restored.choose(cid, act(0, "keep")) == first
    for f in (empty, partial):
        with pytest.raises(GameError, match="保留"):
            restored.restore(f)
    diverged = store_at(tmp_path / "diverged.db")
    diverged.restore(empty)
    diverged.choose(cid, act(0, "lend"))
    diverged.choose(cid, act(1, "return"))
    with pytest.raises(GameError, match="经历不同"):
        restored.restore(diverged.export(cid))
    bad = deepcopy(full)
    bad["commands"][1]["choice"] = "ask"
    with pytest.raises(GameError, match="完整性"):
        restored.restore(bad)
    corrupt = deepcopy(full)
    corrupt["commands"][1]["command_id"] = corrupt["commands"][0]["command_id"]
    with pytest.raises(GameError):
        restored.restore(corrupt)
    assert restored.view(cid) == final


def test_reject_unreachable_credentials_and_scene_errors():
    chapters = sample()
    # Both items exist, but no playthrough can acquire both.
    chapters[1]["scenes"][0]["choices"][0]["requires"] = ["原件", "借据"]
    with pytest.raises(ValueError, match="无法"):
        Book(chapters)
    for defect, regex in [
        ("loop", "循环"),
        ("missing", "未知场景"),
        ("gate", "无门槛"),
        ("orphan", "不可达"),
        ("duplicate", "重复"),
        ("end", "选择分支"),
    ]:
        chapters = sample()
        scene = chapters[0]["scenes"][0]
        if defect == "loop":
            scene["choices"][0]["next"] = "entry"
        if defect == "missing":
            scene["choices"][0]["next"] = "unknown"
        if defect == "gate":
            for c in scene["choices"]:
                c["requires"] = ["原件"]
        if defect == "orphan":
            chapters[0]["scenes"].append(dict(scene, id="detached"))
        if defect == "duplicate":
            scene["choices"][1]["id"] = scene["choices"][0]["id"]
        if defect == "end":
            scene["choices"] = scene["choices"][:1]
        with pytest.raises(ValueError, match=regex):
            Book(chapters)


def test_api_chronicle_and_county_archives_remain_separate(tmp_path, monkeypatch):
    monkeypatch.setattr("game.chronicle.load_book", lambda: Book(sample()))
    county = GameStore(tmp_path / "old.db")
    old = county.create("S01", "老档", "0.500000", "old")
    before = county.export(old["world_id"])
    (tmp_path / "index.html").write_text("fixture")
    client = TestClient(
        make_app(county, "local", tmp_path, 45899),
        base_url="http://127.0.0.1:45899",
        headers={"Authorization": "Bearer local"},
    )
    base = "/api/chronicle"
    assert client.get(base, headers={"Authorization": ""}).status_code == 401
    assert client.get(base).json()["careers"] == []
    assert client.post(base, json={"name": "  "}).status_code == 422
    view = client.post(base, json={"name": " 林 "}).json()
    assert view["name"] == "林"
    href = base + "/" + view["id"]
    assert client.get(href).json() == view
    assert client.get("/api/chronicle/missing").status_code == 404
    body = dict(revision=0, command_id="id", choice="keep")
    assert (
        client.post(href + "/choices", json={**body, "revision": False}).status_code
        == 422
    )
    saved = client.post(href + "/choices", json=body).json()
    assert saved["scene"]["id"] == "entry" and saved["chapter"]["id"] == "b"
    assert client.post(href + "/choices", json=body).json() == saved
    assert (
        client.post(href + "/choices", json={**body, "command_id": "stale"}).status_code
        == 409
    )
    archive = client.get(href + "/export")
    assert "attachment" in archive.headers["Content-Disposition"]
    assert client.post(base + "/import", json=archive.json()).json() == saved
    assert client.post(base + "/import", json=before).status_code == 422
    assert client.post("/api/import", json=archive.json()).status_code == 422
    assert county.export(old["world_id"]) == before
    assert [x["id"] for x in client.get("/api/worlds").json()["worlds"]] == [
        old["world_id"]
    ]


def test_shipped_book_routes_end_and_replay_offline(tmp_path):
    book = load_book()
    store = ChronicleStore(GameStore(tmp_path / "actual.db"), book)
    for index in [0, -1]:
        view = store.create("传家记")
        for rev in range(book.max_commands):
            if view["finished"]:
                break
            choice = view["scene"]["choices"][index]
            view = store.choose(view["id"], act(rev, choice["id"]))
        assert view["finished"] and view["chapter"]["id"] == book.chapters[-1].id
        assert list(dict.fromkeys(row["chapter_id"] for row in view["journal"])) == [
            ch.id for ch in book.chapters
        ]
        assert store.restore(store.export(view["id"])) == view


def test_chronicle_fork_before_choice_retains_only_selected_history(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("game.chronicle.load_book", lambda: Book(sample()))
    (tmp_path / "index.html").write_text("fixture")
    client = TestClient(
        make_app(GameStore(tmp_path / "game.db"), "local", tmp_path, 45899),
        base_url="http://127.0.0.1:45899",
        headers={"Authorization": "Bearer local"},
    )
    base = "/api/chronicle"
    original = client.post(base, json={"name": "家书"}).json()
    path = base + "/" + original["id"]
    one = client.post(path + "/choices", json=act(0, "keep").model_dump()).json()
    final = client.post(path + "/choices", json=act(1, "file").model_dump()).json()
    old_file = client.get(path + "/export").json()
    assert client.post(path + "/fork", json={"revision": 3}).status_code == 409
    assert client.post(path + "/fork", json={"revision": -1}).status_code == 422
    assert len(client.get(base).json()["careers"]) == 1
    branch = client.post(path + "/fork", json={"revision": 1, "name": "另一封"}).json()
    assert (
        branch == {**one, "id": branch["id"], "name": "另一封"}
        and branch["id"] != one["id"]
    )
    second = client.post(
        base + "/" + branch["id"] + "/choices", json=act(1, "ask").model_dump()
    ).json()
    assert (
        second["finished"]
        and second["marks"] == ["原件"]
        and final["marks"] == ["原件", "旁注"]
    )
    blank = client.post(path + "/fork", json={"revision": 0}).json()
    assert (
        blank["marks"] == blank["journal"] == [] and blank["scene"] == original["scene"]
    )
    assert (
        client.get(path + "/export").json() == old_file
        and client.get(path).json() == final
    )


def test_desktop_restore_file_routes_both_formats_to_their_original_career(
    tmp_path, monkeypatch
):
    from main import restore_archive

    monkeypatch.setattr("game.chronicle.load_book", lambda: Book(sample()))
    first = GameStore(tmp_path / "source.db")
    chron = ChronicleStore(first, Book(sample()))
    v = chron.create("随身册")
    v = chron.choose(v["id"], act(0, "keep"))
    county = first.create("S02", "县档", "0.500000", "before")
    county_data = first.export(county["world_id"])
    after = GameStore(tmp_path / "new.db")
    for archive in (chron.export(v["id"]), county_data):
        file = tmp_path / "backup.json"
        file.write_text(json.dumps(archive, ensure_ascii=False), encoding="utf8")
        restore_archive(after, file)
    assert ChronicleStore(after).view(v["id"]) == v
    assert after.export(county["world_id"]) == county_data


def test_saved_decisions_survive_editorial_changes_but_reject_changed_earned_credentials(
    tmp_path,
):
    db = GameStore(tmp_path / "working.db")
    first = ChronicleStore(db, Book(sample()))
    cid = first.create("家书")["id"]
    before = first.choose(cid, act(0, "keep"))
    archive = first.export(cid)
    revised = sample()
    action = revised[0]["scenes"][0]["choices"][0]
    action.update(result="修订措辞", tone="turn")
    second = ChronicleStore(db, Book(revised))
    after = second.view(cid)
    assert before["marks"] == after["marks"] and before["scene"] == after["scene"]
    assert (
        after["journal"][0]["result"] == "修订措辞"
        and after["journal"][0]["tone"] == "turn"
    )
    assert second.restore(archive) == after
    changed = deepcopy(revised)
    changed[0]["scenes"][0]["choices"][0]["marks"].append("新增条件")
    third = ChronicleStore(db, Book(changed))
    with pytest.raises(GameError, match="版本校验"):
        third.view(cid)
    assert second.view(cid) == after


@pytest.mark.parametrize(
    "load_campaign", [load_book, load_witness], ids=["family", "witness"]
)
def test_authored_routes_have_playable_witnesses_and_locked_choices_stay_hidden(
    load_campaign,
):
    from collections import defaultdict
    from functools import cache

    book = load_campaign()
    opening = [(i, ch.scenes[0].id) for i, ch in enumerate(book.chapters)]
    incoming = defaultdict(list)
    authored = []
    for i, chapter in enumerate(book.chapters):
        for scene in chapter.scenes:
            for choice in scene.choices:
                source = (i, scene.id)
                authored.append((source, choice))
                if choice.next != "END":
                    target = (i, choice.next)
                elif i + 1 < len(opening):
                    target = opening[i + 1]
                else:
                    continue
                incoming[target].append((source, choice))

    @cache
    def possible_before(target):
        return frozenset().union(
            *(
                possible_before(source).union(previous.marks)
                for source, previous in incoming[target]
            )
        )

    @cache
    def witness(target, required, forbidden=None):
        # Work backward through the acyclic story. Each subproblem tracks only
        # the receipts needed for this one choice. Unrelated combinations of
        # earlier receipts cannot enlarge the search. Keeping a receipt absent
        # forbids any step that awards it, even in earlier chapters.
        if forbidden in required or not required <= possible_before(target):
            return None
        if target == opening[0]:
            return () if not required else None
        for source, previous in incoming[target]:
            if forbidden in previous.marks:
                continue
            earlier = required.difference(previous.marks).union(previous.requires)
            prefix = witness(source, earlier, forbidden)
            if prefix is not None:
                return prefix + (previous.id,)
        return None

    @cache
    def state_after(route):
        if not route:
            return book.beginning()
        prev = state_after(route[:-1])
        state = {**prev, "journal": list(prev["journal"]), "marks": list(prev["marks"])}
        book.advance(state, route[-1])
        return state

    for position, choice in authored:
        path = witness(position, frozenset(choice.requires))
        assert path is not None, (position, choice.id)
        before = state_after(path)
        assert (before["chapter"], before["scene"]) == position
        public = book.view("id", "档案", before)
        assert choice.id in [c["id"] for c in public["scene"]["choices"]]
        committed = state_after(path + (choice.id,))["journal"][-1]
        assert committed["result"] == choice.result
        assert set(committed["marks"]) == set(choice.marks).difference(before["marks"])
        if choice.requires:
            negative = next(
                (
                    p
                    for req in choice.requires
                    if (p := witness(position, frozenset(), req)) is not None
                ),
                None,
            )
            if negative is None:
                # Some scenes only exist after their receipt has been earned, e.g.
                # signing the dated agreement before the release hearing. Verify
                # the defensive rule separately from the witnessed legal route.
                assert book.campaign == "witness", (position, choice.id)
                locked = {
                    **before,
                    "marks": [m for m in before["marks"] if m not in choice.requires],
                }
            else:
                locked = state_after(negative)
            assert choice.id not in [
                c["id"] for c in book.view("id", "档案", locked)["scene"]["choices"]
            ]
            with pytest.raises(GameError, match="可用"):
                book.advance(locked, choice.id)
