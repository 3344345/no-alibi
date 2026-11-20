"""Offline, event-sourced historical campaigns and their portable saves."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from copy import copy, deepcopy
from functools import cached_property
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from game.balance import canonical
from game.chronicle_editions import legacy_books
from game.chronicle_serial import SERIAL_EDITION, SERIAL_STAGES, serial_chapters
from game.engine import GameError


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


Text = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Short = Annotated[
    str, StringConstraints(min_length=1, max_length=128, strip_whitespace=True)
]
CareerName = Annotated[
    str, StringConstraints(min_length=1, max_length=48, strip_whitespace=True)
]
Campaign = Literal["family", "witness"]
Tone = Literal["setback", "evidence", "turn"]


class Source(Strict):
    name: Text
    url: Text


class Exhibit(Strict):
    id: Short
    title: Text
    detail: Text


class Choice(Strict):
    id: Short
    label: Text
    result: Text
    next: Short
    marks: list[Short] = Field(default_factory=list)
    requires: list[Short] = Field(default_factory=list)
    tone: Tone | None = None
    cites: list[Short] = Field(default_factory=list)


class Echo(Strict):
    mark: Short
    body: Text


class Scene(Strict):
    id: Short
    title: Text
    body: Text
    choices: list[Choice] = Field(min_length=1)
    exhibits: list[Exhibit] = Field(default_factory=list)
    echoes: list[Echo] = Field(default_factory=list)


class Chapter(Strict):
    id: Short
    year: Text
    place: Text
    title: Text
    role: Text
    intro: Text
    history: Text
    sources: list[Source] = Field(min_length=1)
    scenes: list[Scene] = Field(min_length=1)


class NewChronicle(Strict):
    name: CareerName
    campaign: Campaign = "family"
    start_chapter: Short | None = None
    opening_choice: Short | None = None
    edition: Literal["serial_v1"] | None = None


class Branch(Strict):
    revision: int = Field(ge=0)
    name: CareerName | None = None


class Command(Strict):
    revision: int = Field(ge=0)
    command_id: Short
    choice: Short


class Archive(Strict):
    format: Literal[
        "juzhongshi-chronicle/1", "juzhongshi-chronicle/2", "juzhongshi-chronicle/3"
    ]
    chapters: list[Short] | None = None
    campaign: Campaign = "family"
    start_chapter: Short | None = None
    id: str = Field(pattern=r"^[0-9a-f]{32}$")
    name: CareerName
    commands: list[Command]
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")


def _unique(values, where):
    if len(values) != len(set(values)):
        raise ValueError(f"{where} 使用了重复编号")


def _postorder(ch, scenes):
    order, done, visiting = [], set(), set()

    def visit(sid):
        if sid in visiting:
            raise ValueError(f"{ch.id}/{sid} 路线循环")
        if sid in done or sid == "END":
            return
        visiting.add(sid)
        for c in scenes[sid].choices:
            visit(c.next)
        visiting.remove(sid)
        done.add(sid)
        order.append(sid)

    visit(ch.scenes[0].id)
    if done != set(scenes):
        raise ValueError(f"{ch.id} 有不可达场景")
    return order


class Book:
    def __init__(self, chapters, campaign: Campaign = "family", edition=None):
        self.edition = edition
        self.campaign = campaign
        self.chapters = tuple(Chapter.model_validate(ch) for ch in chapters)
        if not self.chapters:
            raise ValueError("至少需要一章")
        _unique([ch.id for ch in self.chapters], "章节")
        self.indices = {ch.id: i for i, ch in enumerate(self.chapters)}
        self.scene_maps = [{s.id: s for s in ch.scenes} for ch in self.chapters]
        self.destinations = {
            (ch.id, scene.id, c.id): c.next
            for ch in self.chapters
            for scene in ch.scenes
            for c in scene.choices
        }
        self.max_commands = sum(len(ch.scenes) for ch in self.chapters)
        self._validate_routes()

    @property
    def manifest(self):
        if self.edition:
            return tuple(f"{self.edition}/{cid}" for cid in self.indices)
        return tuple(self.indices)

    def _validate_routes(self):
        # Marks never expire. A superset can enable every future route of its subset.
        # Discard unused marks and dominated alternatives so independent chapter choices
        # do not expand into the entire Cartesian product of past playthroughs.
        future = [frozenset() for _ in range(len(self.chapters) + 1)]
        for i in reversed(range(len(self.chapters))):
            scenes = self.chapters[i].scenes
            future[i] = future[i + 1].union(
                (m for scene in scenes for choice in scene.choices for m in choice.requires),
                (e.mark for scene in scenes for e in scene.echoes),
            )
        entry = {frozenset()}
        for i, (ch, scenes) in enumerate(
            zip(self.chapters, self.scene_maps, strict=True)
        ):
            if len(scenes) != len(ch.scenes) or "END" in scenes:
                raise ValueError(f"{ch.id} 场景编号重复或保留")
            if not any(len(scene.choices) > 1 for scene in ch.scenes):
                raise ValueError(f"{ch.id} 缺少选择分支")
            for source in ch.sources:
                parsed = urlsplit(source.url)
                if parsed.scheme not in ("https", "http") or not parsed.hostname:
                    raise ValueError(f"{ch.id} 资料链接无效")
            for s in ch.scenes:
                _unique([c.id for c in s.choices], f"{ch.id}/{s.id}")
                _unique([e.mark for e in s.echoes], f"{ch.id}/{s.id} 后续叙事")
                exhibit_ids = [e.id for e in s.exhibits]
                _unique(exhibit_ids, f"{ch.id}/{s.id} 案头材料")
                for c in s.choices:
                    if c.cites and (
                        len(set(c.cites)) != 2
                        or len(c.cites) != 2
                        or not set(c.cites) <= set(exhibit_ids)
                    ):
                        raise ValueError(f"{ch.id}/{s.id}/{c.id} 引用材料无效")
                if all(c.requires for c in s.choices):
                    raise ValueError(f"{ch.id}/{s.id} 缺少无门槛选择")
                for c in s.choices:
                    if c.next != "END" and c.next not in scenes:
                        raise ValueError(f"{ch.id}/{s.id}/{c.id} 指向未知场景")
            order = _postorder(ch, scenes)
            needed = {"END": future[i + 1]}
            for sid in order:
                needed[sid] = frozenset().union(
                    *(needed[c.next].union(c.requires) for c in scenes[sid].choices),
                    (e.mark for e in scenes[sid].echoes),
                )
            states = defaultdict(set)
            states[ch.scenes[0].id] = entry
            for sid in reversed(order):
                variants = states.pop(sid)
                for echo in scenes[sid].echoes:
                    if not any(echo.mark in marks for marks in variants):
                        raise ValueError(f"{ch.id}/{sid} 的后续叙事缺少可取得的凭据：{echo.mark}")
                for c in scenes[sid].choices:
                    possible = [m for m in variants if m.issuperset(c.requires)]
                    if not possible:
                        raise ValueError(
                            f"{ch.id}/{sid}/{c.id} 的凭据无法从此前路线取得"
                        )
                    out = states[c.next]
                    for m in possible:
                        acquired = m.union(c.marks).intersection(needed[c.next])
                        if any(existing >= acquired for existing in out):
                            continue
                        out.difference_update(
                            {existing for existing in out if existing < acquired}
                        )
                        out.add(acquired)
            entry = states["END"]

    def in_order(self, order):
        if order == tuple(self.indices):
            return self
        if (
            not order
            or len(set(order)) != len(order)
            or any(cid not in self.indices for cid in order)
        ):
            raise GameError(
                "invalid_archive", "这份长篇的章节目录不完整或使用了未知章节。"
            )
        indices = [self.indices[cid] for cid in order]
        if indices != sorted(indices):
            raise GameError("invalid_archive", "这份长篇的章节顺序不符合该战役年表。")
        edition = copy(self)
        edition.chapters = tuple(self.chapters[i] for i in indices)
        edition.scene_maps = [self.scene_maps[i] for i in indices]
        edition.indices = {ch.id: i for i, ch in enumerate(edition.chapters)}
        edition.max_commands = sum(map(len, edition.scene_maps))
        return edition

    def beginning(self, start_chapter=None):
        if start_chapter is None:
            index = 0
        elif start_chapter in self.indices:
            index = self.indices[start_chapter]
        else:
            raise GameError("invalid_input", "所选起点不属于这部历史长篇。")
        return {
            "start_chapter": self.chapters[index].id,
            "chapter": index,
            "scene": self.chapters[index].scenes[0].id,
            "journal": [],
            "marks": [],
        }

    def advance(self, state, choice_id):
        i = state["chapter"]
        ch = self.chapters[i]
        if state["scene"] is None:
            raise GameError("finished", "这份长篇档案已经写完。")
        scene = self.scene_maps[i][state["scene"]]
        owned = set(state["marks"])
        choice = next(
            (
                c
                for c in scene.choices
                if c.id == choice_id and owned.issuperset(c.requires)
            ),
            None,
        )
        if choice is None:
            raise GameError("unavailable", "请从当前场景里可用的选择中决定。")
        gained = list(dict.fromkeys(m for m in choice.marks if m not in owned))
        event = {
            "chapter_id": ch.id,
            "year": ch.year,
            "place": ch.place,
            "role": ch.role,
            "scene": scene.id,
            "title": scene.title,
            "choice": choice.id,
            "label": choice.label,
            "result": choice.result,
            "marks": gained,
        }
        if choice.cites:
            event["citations"] = [
                e.model_dump() for e in scene.exhibits if e.id in choice.cites
            ]
        if choice.tone:
            event["tone"] = choice.tone
        state["journal"].append(event)
        state["marks"].extend(gained)
        if choice.next != "END":
            state["scene"] = choice.next
        elif i + 1 < len(self.chapters):
            state["chapter"] += 1
            state["scene"] = self.chapters[i + 1].scenes[0].id
        else:
            state["scene"] = None
        return event

    def event_hash(self, event):
        # Actions, earned credentials and the route are durable. Text, citations
        # and soundtrack cues may receive editorial corrections between releases.
        key = (event["chapter_id"], event["scene"], event["choice"])
        return _digest([*key, self.destinations[key], event["marks"]])

    def view(self, cid, name, state):
        i = state["chapter"]
        ch = self.chapters[i]
        sid = state["scene"]
        scene = None
        if sid is not None:
            current = self.scene_maps[i][sid]
            owned = set(state["marks"])
            callbacks = [echo for echo in current.echoes if echo.mark in owned]
            scene = {
                "id": sid,
                **(
                    {"exhibits": [e.model_dump() for e in current.exhibits]}
                    if current.exhibits
                    else {}
                ),
                "title": current.title,
                "body": "\n\n".join(
                    [current.body, *(e.body for e in callbacks)]
                ),
                "choices": [
                    {
                        "id": c.id,
                        "label": c.label,
                        **({"cites": c.cites} if c.cites else {}),
                    }
                    for c in current.choices
                    if owned.issuperset(c.requires)
                ],
            }
            if callbacks:
                origins = {
                    mark: index for index, entry in enumerate(state["journal"])
                    for mark in entry["marks"]
                }
                scene["base_body"] = current.body
                scene["callbacks"] = [
                    {"body": echo.body, "origin": origins[echo.mark]} for echo in callbacks
                ]
        return {
            "id": cid,
            "name": name,
            "campaign": self.campaign,
            **({"edition": self.edition} if self.edition else {}),
            "start_chapter": state["start_chapter"],
            "chapter_count": len(self.chapters),
            "revision": len(state["journal"]),
            "finished": sid is None,
            "chapter": ch.model_dump(exclude={"scenes"}),
            "scene": scene,
            "journal": deepcopy(state["journal"]),
            "marks": list(state["marks"]),
        }


def load_book():
    # Literal imports also let the desktop packager discover both content modules.
    from game.chronicle_cases import attach_desks
    from game.chronicle_early import CHAPTERS as early
    from game.chronicle_late import CHAPTERS as late

    return Book(attach_desks([*early, *late]))


def load_witness():
    from game.witness_civic import CHAPTERS as civic
    from game.witness_deng import CHAPTERS as deng
    from game.witness_early import CHAPTERS as early
    from game.witness_late import CHAPTERS as late
    from game.witness_public import CHAPTERS as public
    from game.witness_reform import CHAPTERS as reform
    from game.witness_republic import CHAPTERS as republic

    chapters = sorted(
        [*early, *deng, *late, *civic, *reform, *republic, *public],
        key=lambda chapter: int(chapter["year"][:4]),
    )
    return Book(chapters, "witness")


def _digest(payload):
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


class ChronicleStore:
    def __init__(self, game_store, book=None):
        self.database = game_store
        if book is not None:
            self.book = book
        with game_store._db(write=True) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS chronicle_careers (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                campaign TEXT NOT NULL DEFAULT 'family', start_chapter TEXT, chapter_order TEXT)""")
            columns = {
                r["name"] for r in db.execute("PRAGMA table_info(chronicle_careers)")
            }
            if "campaign" not in columns:
                db.execute(
                    "ALTER TABLE chronicle_careers ADD COLUMN campaign TEXT NOT NULL DEFAULT 'family'"
                )
            if "start_chapter" not in columns:
                db.execute(
                    "ALTER TABLE chronicle_careers ADD COLUMN start_chapter TEXT"
                )
            if "chapter_order" not in columns:
                db.execute(
                    "ALTER TABLE chronicle_careers ADD COLUMN chapter_order TEXT"
                )
            db.execute("""CREATE TABLE IF NOT EXISTS chronicle_choices (
                career TEXT NOT NULL REFERENCES chronicle_careers(id),
                revision INTEGER NOT NULL CHECK(revision>=0), command_id TEXT NOT NULL,
                choice TEXT NOT NULL, event_hash TEXT NOT NULL,
                PRIMARY KEY(career,revision), UNIQUE(career,command_id))""")

            # Resolve legacy SQLite histories against the actual pre-manifest releases.
            # A damaged career stays readable only through its explicit integrity error;
            # it must not block opening other saves or the county game.
            for row in db.execute(
                "SELECT id,name,campaign,start_chapter,chapter_order FROM chronicle_careers WHERE chapter_order IS NULL"
            ).fetchall():
                try:
                    old = self._saved_book(row, self._rows(db, row["id"]))
                except GameError:
                    continue
                db.execute(
                    "UPDATE chronicle_careers SET chapter_order=?,start_chapter=? WHERE id=?",
                    (
                        canonical(list(old.manifest)),
                        row["start_chapter"] or old.chapters[0].id,
                        row["id"],
                    ),
                )

    @cached_property
    def book(self):
        return load_book()

    @cached_property
    def witness(self):
        return load_witness()

    @cached_property
    def serial(self):
        return Book(serial_chapters(self.witness), "witness", SERIAL_EDITION)

    def _from_manifest(self, full, order, start):
        if order and order[0].startswith(SERIAL_EDITION + "/"):
            if full.campaign == "witness" and start == SERIAL_STAGES[0][0] and order == self.serial.manifest:
                return self.serial
            raise GameError("invalid_archive", "年代连演的五章次序或起点有误。")
        return full.in_order(order)

    def _book(self, campaign):
        if campaign == "family":
            return self.book
        if campaign == "witness":
            return self.witness
        raise GameError("invalid_input", "找不到所选长篇。")

    @staticmethod
    def _career(db, cid):
        head = db.execute(
            "SELECT name,campaign,start_chapter,chapter_order FROM chronicle_careers WHERE id=?",
            (cid,),
        ).fetchone()
        if head is None:
            raise GameError("not_found", "未找到这份长篇档案。")
        return head

    @staticmethod
    def _rows(db, cid):
        return db.execute(
            "SELECT revision,command_id,choice,event_hash FROM chronicle_choices WHERE career=? ORDER BY revision",
            (cid,),
        ).fetchall()

    def _saved_book(self, head, rows):
        full = self._book(head["campaign"])
        if head["chapter_order"] is not None:
            try:
                order = json.loads(head["chapter_order"])
                if not isinstance(order, list) or not all(
                    isinstance(cid, str) for cid in order
                ):
                    raise ValueError
            except ValueError as exc:
                raise GameError("invalid_archive", "本地章节目录损坏。") from exc
            return self._from_manifest(full, tuple(order), head["start_chapter"])
        for candidate in legacy_books(full):
            try:
                self._replay(candidate, head["start_chapter"], rows)
                return candidate
            except GameError:
                continue
        raise GameError("invalid_archive", "这份旧档的历史与已发行的章节次序不符。")

    def _replay(self, book, start, rows):
        state = book.beginning(start)
        for i, row in enumerate(rows):
            if row["revision"] != i:
                raise GameError("invalid_archive", "长篇档案的章节记录不连续。")
            event = book.advance(state, row["choice"])
            if row["event_hash"] not in (book.event_hash(event), _digest(event)):
                raise GameError("invalid_archive", "长篇档案的选择结果未通过版本校验。")
        return state

    def catalogue(self, campaign="family"):
        book = self._book(campaign)
        chapters = [ch.model_dump(exclude={"scenes"}) for ch in book.chapters]
        careers = []
        with self.database._db(snapshot=True) as db:
            for head in db.execute(
                "SELECT id,name,campaign,start_chapter,chapter_order FROM chronicle_careers WHERE campaign=? ORDER BY rowid DESC",
                (campaign,),
            ):
                rows = self._rows(db, head["id"])
                book = self._saved_book(head, rows)
                state = self._replay(book, head["start_chapter"], rows)
                careers.append(
                    dict(
                        {
                            k: head[k]
                            for k in ("id", "name", "campaign", "start_chapter")
                        },
                        opening_choice=rows[0]["choice"] if rows else None,
                        standalone=len(book.chapters) == 1,
                        **({"edition": book.edition} if book.edition else {}),
                        revision=len(state["journal"]),
                        chapter_id=book.chapters[state["chapter"]].id,
                        finished=state["scene"] is None,
                        **({"outcomes": [
                            {key: entry[key] for key in ("chapter_id", "label", "result", "marks")}
                            for entry in state["journal"]
                            if book.destinations[(entry["chapter_id"], entry["scene"], entry["choice"])] == "END"
                        ]} if campaign == "witness" else {}),
                    )
                )
        return {"chapters": chapters, "careers": careers}

    def create(self, name, campaign="family", start_chapter=None, opening_choice=None, edition=None):
        req = NewChronicle(name=name, campaign=campaign, start_chapter=start_chapter, opening_choice=opening_choice, edition=edition)
        name = req.name
        if req.edition and (campaign != "witness" or req.start_chapter or req.opening_choice):
            raise GameError("invalid_input", "年代连演从西安开场，请在历史亲历者模式中开卷。")
        book = self.serial if req.edition else self._book(req.campaign)
        if campaign == "family" and start_chapter is not None:
            raise GameError("invalid_input", "市井家书从第一章开卷。")
        if req.opening_choice and campaign == "witness":
            if not req.start_chapter:
                raise GameError("invalid_input", "请选择人物长篇的起点。")
            book = book.in_order((req.start_chapter,))
        state = book.beginning(req.start_chapter)
        start = state["start_chapter"]
        cid = uuid4().hex
        with self.database._db(write=True) as db:
            db.execute(
                "INSERT INTO chronicle_careers(id,name,campaign,start_chapter,chapter_order) VALUES(?,?,?,?,?)",
                (cid, name, campaign, start, canonical(list(book.manifest))),
            )
            if req.opening_choice:
                command = Command(revision=0, command_id=uuid4().hex, choice=req.opening_choice)
                self._record(db, book, cid, command, book.advance(state, command.choice))
        return book.view(cid, name, state)

    def view(self, cid):
        with self.database._db(snapshot=True) as db:
            head = self._career(db, cid)
            rows = self._rows(db, cid)
            book = self._saved_book(head, rows)
            return book.view(
                cid,
                head["name"],
                self._replay(book, head["start_chapter"], rows),
            )

    def _record(self, db, book, cid, cmd, event):
        db.execute(
            "INSERT INTO chronicle_choices(career,revision,command_id,choice,event_hash) VALUES(?,?,?,?,?)",
            (
                cid,
                cmd.revision,
                cmd.command_id,
                cmd.choice,
                book.event_hash(event),
            ),
        )

    def choose(self, cid, cmd):
        with self.database._db(write=True) as db:
            head = self._career(db, cid)
            name, start = head["name"], head["start_chapter"]
            rows = self._rows(db, cid)
            book = self._saved_book(head, rows)
            receipt = next((r for r in rows if r["command_id"] == cmd.command_id), None)
            if receipt is not None:
                if (
                    receipt["revision"] != cmd.revision
                    or receipt["choice"] != cmd.choice
                ):
                    raise GameError(
                        "idempotency_conflict", "这项选择的回执已用于另一份请求。"
                    )
                return book.view(
                    cid, name, self._replay(book, start, rows[: cmd.revision + 1])
                )
            if len(rows) != cmd.revision:
                raise GameError("revision_conflict", "档案已更新，请重新查看当前场景。")
            state = self._replay(book, start, rows)
            self._record(db, book, cid, cmd, book.advance(state, cmd.choice))
            return book.view(cid, name, state)

    def fork(self, cid, branch):
        with self.database._db(write=True) as db:
            head = self._career(db, cid)
            old_name, start = head["name"], head["start_chapter"]
            rows = self._rows(db, cid)
            book = self._saved_book(head, rows)
            if branch.revision > len(rows):
                raise GameError("revision_conflict", "这份档案还没有走到所选位置。")
            new_id = uuid4().hex
            name = branch.name if branch.name else old_name[:43] + " · 分线"
            state = self._replay(book, start, rows[: branch.revision])
            db.execute(
                "INSERT INTO chronicle_careers(id,name,campaign,start_chapter,chapter_order) VALUES(?,?,?,?,?)",
                (new_id, name, head["campaign"], start, canonical(list(book.manifest))),
            )
            db.execute(
                """INSERT INTO chronicle_choices(career,revision,command_id,choice,event_hash)
                          SELECT ?,revision,command_id,choice,event_hash FROM chronicle_choices
                          WHERE career=? AND revision<? ORDER BY revision""",
                (new_id, cid, branch.revision),
            )
            return book.view(new_id, name, state)

    def export(self, cid):
        with self.database._db(snapshot=True) as db:
            head = self._career(db, cid)
            name, start = head["name"], head["start_chapter"]
            rows = self._rows(db, cid)
            book = self._saved_book(head, rows)
            state = self._replay(book, start, rows)
            commands = [
                {
                    "revision": r["revision"],
                    "command_id": r["command_id"],
                    "choice": r["choice"],
                }
                for r in rows
            ]
            payload = {
                "format": "juzhongshi-chronicle/3",
                "campaign": head["campaign"],
                "start_chapter": state["start_chapter"],
                "chapters": list(book.manifest),
                "id": cid,
                "name": name,
                "commands": commands,
            }
            # Fingerprint only the actual path. Unvisited revisions to other scenes do
            # not invalidate a file, and unchosen outcomes never enter the export.
            payload["checksum"] = _digest(
                [payload, [book.event_hash(e) for e in state["journal"]]]
            )
            return payload

    def restore(self, data):
        try:
            archive = Archive.model_validate(data)
        except ValidationError as exc:
            raise GameError("invalid_archive", "文件格式或版本有误。") from exc
        full = self._book(archive.campaign)
        if archive.format == "juzhongshi-chronicle/3":
            if (
                not {"chapters", "campaign", "start_chapter"}
                <= archive.model_fields_set
                or not archive.start_chapter
                or not archive.chapters
            ):
                raise GameError("invalid_archive", "长篇存档缺少战役、章节年表或起点。")
            candidates = [self._from_manifest(full, tuple(archive.chapters), archive.start_chapter)]
            if (
                archive.campaign == "family"
                and archive.start_chapter != archive.chapters[0]
            ):
                raise GameError("invalid_archive", "市井家书的开卷位置无效。")
        else:
            if "chapters" in archive.model_fields_set:
                raise GameError("invalid_archive", "旧格式不含章节目录。")
            if (
                archive.format == "juzhongshi-chronicle/1"
                and {"campaign", "start_chapter"} & archive.model_fields_set
            ):
                raise GameError("invalid_archive", "旧格式仅用于市井家书。")
            if archive.format == "juzhongshi-chronicle/2" and (
                archive.campaign != "witness" or not archive.start_chapter
            ):
                raise GameError("invalid_archive", "亲历者存档缺少战役或起点。")
            candidates = legacy_books(full)
        commands = archive.commands
        if len({c.command_id for c in commands}) != len(commands) or any(
            c.revision != i for i, c in enumerate(commands)
        ):
            raise GameError("invalid_archive", "选择回执重复或记录不连续。")
        payload = archive.model_dump(exclude={"checksum"}, exclude_unset=True)
        for book in candidates:
            if len(commands) > book.max_commands:
                continue
            try:
                state = book.beginning(archive.start_chapter)
                for c in commands:
                    book.advance(state, c.choice)
            except GameError:
                continue
            hashes = [book.event_hash(e) for e in state["journal"]]
            legacy_hashes = [_digest(e) for e in state["journal"]]
            if archive.checksum in (
                _digest([payload, hashes]),
                _digest([payload, legacy_hashes]),
            ):
                break
        else:
            raise GameError(
                "invalid_archive", "这份文件的章节顺序和选择未通过完整性校验。"
            )
        start = state["start_chapter"]
        with self.database._db(write=True) as db:
            head = db.execute(
                "SELECT name,campaign,start_chapter,chapter_order FROM chronicle_careers WHERE id=?",
                (archive.id,),
            ).fetchone()
            rows = self._rows(db, archive.id)
            if head and (
                head["name"] != archive.name
                or head["campaign"] != archive.campaign
                or (head["start_chapter"] or book.chapters[0].id) != start
                or self._saved_book(head, rows).manifest != book.manifest
                or len(rows) > len(commands)
            ):
                raise GameError(
                    "history_conflict", "本机已有更新或不同的档案，已保留原记录。"
                )
            for i, r in enumerate(rows):
                c = commands[i]
                if (r["revision"], r["command_id"], r["choice"]) != (
                    i,
                    c.command_id,
                    c.choice,
                ) or r["event_hash"] not in (hashes[i], legacy_hashes[i]):
                    raise GameError(
                        "history_conflict", "文件里的选择与本机经历不同，已保留原记录。"
                    )
            if not head:
                db.execute(
                    "INSERT INTO chronicle_careers(id,name,campaign,start_chapter,chapter_order) VALUES(?,?,?,?,?)",
                    (
                        archive.id,
                        archive.name,
                        archive.campaign,
                        start,
                        canonical(list(book.manifest)),
                    ),
                )
            for i in range(len(rows), len(commands)):
                self._record(db, book, archive.id, commands[i], state["journal"][i])
            return book.view(archive.id, archive.name, state)
