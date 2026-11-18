"""SQLite committer. Each committed decision seals event bytes and projection effects.

Replay applies those effects in order; only an explicit live command runs game rules.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Annotated

from pydantic import Field, JsonValue

from . import balance as bal
from . import catalog, engine, event_protocol, outbox, world_projects
from .engine import GameError, checked

SAVE_VERSION = "juzhongshi-save/1"
RULE_VERSION = "juzhongshi-engine/4.0.0"
CONTENT_HASH = bal.digest(
    {
        "catalog": {k: v for k, v in vars(catalog).items() if k.isupper()},
        "budget_plans": world_projects.PLANS,
        "report_variants": world_projects.VARIANTS,
    }
)
VERSION = {
    "format": SAVE_VERSION,
    "rules": RULE_VERSION,
    "content": catalog.VERSION,
    "content_hash": CONTENT_HASH,
    "parameter_package_hash": bal.PACKAGE_HASH,
    "calculation_version": bal.CALC_VERSION,
    "rng_version": "sha256-midpoint52/1",
    "prompt_version": "offline-candidates/1",
    "application": "4.0.0",
}
ZERO = "0" * 64
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)]


class Entry(bal.Strict):
    revision: bal.Minute
    previous: Hash
    command: dict[str, JsonValue]
    events: list[dict[str, JsonValue]]
    effects: list[list[JsonValue]]
    state_hash: Hash
    checksum: Hash


class SavedReceipt(bal.Strict):
    id: bal.Name
    request_hash: Hash
    revision: bal.Minute


class Manifest(bal.Strict):
    format: str
    rules: str
    content: str
    content_hash: Hash
    parameter_package_hash: Hash
    calculation_version: str
    rng_version: str
    prompt_version: str
    application: str
    world_id: bal.Name
    world_revision: bal.Minute
    last_event_sequence: bal.Minute
    snapshot_hash: Hash
    genesis_seed: Annotated[str, Field(min_length=1, max_length=128)]
    parent_world_id: bal.Name | None
    fork_revision: bal.Minute | None


class SavedWorld(bal.Strict):
    manifest: Manifest
    world_id: bal.Name
    revision: bal.Minute
    history: Annotated[list[Entry], Field(min_length=1)]
    receipts: list[SavedReceipt]
    checksum: Hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS careers(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, start TEXT NOT NULL, minute INTEGER NOT NULL,
 revision INTEGER NOT NULL, projection TEXT NOT NULL, chain TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS journal(
 world TEXT NOT NULL REFERENCES careers(id), revision INTEGER NOT NULL,
 value TEXT NOT NULL, PRIMARY KEY(world,revision)
);
CREATE TABLE IF NOT EXISTS receipts(
 world TEXT NOT NULL REFERENCES careers(id), id TEXT NOT NULL, request_hash TEXT NOT NULL,
 revision INTEGER NOT NULL, PRIMARY KEY(world,id),
 FOREIGN KEY(world,revision) REFERENCES journal(world,revision)
);
CREATE TABLE IF NOT EXISTS restored_versions(
 source_id TEXT NOT NULL, archive_hash TEXT NOT NULL, target_world TEXT NOT NULL REFERENCES careers(id),
 initial_revision INTEGER NOT NULL, PRIMARY KEY(source_id,archive_hash)
);
CREATE TABLE IF NOT EXISTS snapshots(
 world TEXT NOT NULL REFERENCES careers(id), revision INTEGER NOT NULL, value TEXT NOT NULL,
 PRIMARY KEY(world,revision), FOREIGN KEY(world,revision) REFERENCES journal(world,revision)
);
CREATE TRIGGER IF NOT EXISTS journal_no_update BEFORE UPDATE ON journal
 BEGIN SELECT RAISE(ABORT,'immutable game history'); END;
CREATE TRIGGER IF NOT EXISTS journal_no_delete BEFORE DELETE ON journal
 BEGIN SELECT RAISE(ABORT,'immutable game history'); END;
"""


def _diff(old, new, path=()):
    if old == new:
        return
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() - new.keys()):
            yield ["remove", [*path, key]]
        for key in sorted(new):
            if key not in old:
                yield ["set", [*path, key], new[key]]
            else:
                yield from _diff(old[key], new[key], (*path, key))
        return
    if isinstance(old, list) and isinstance(new, list):
        if len(new) >= len(old) and new[: len(old)] == old:
            yield ["append", list(path), new[len(old) :]]
            return
        # The bounded visible journal discards its oldest entries as new ones
        # arrive. Record the slide without embedding 199 unmodified messages.
        if path == ("timeline",) and new:
            match = next(
                (i for i, e in enumerate(old) if e["id"] == new[0]["id"]), None
            )
            if match and old[match:] == new[: len(old) - match]:
                yield ["slide", list(path), match, new[len(old) - match :]]
                return
    yield ["set", list(path), new]


def _apply(state, effects):
    for op in effects:
        kind, path, *args = op
        if not isinstance(path, list) or any(type(x) is not str for x in path):
            raise ValueError("存档效果路径无效")
        if not path:
            if (
                kind != "set"
                or len(args) != 1
                or not isinstance(args[0], dict)
                or state is not None
            ):
                raise ValueError("存档起始效果无效")
            state = deepcopy(args[0])
            continue
        target = state
        for key in path[:-1]:
            target = target[key]
        key = path[-1]
        if kind == "remove" and not args:
            del target[key]
        elif kind == "set" and len(args) == 1:
            target[key] = deepcopy(args[0])
        elif kind == "append" and len(args) == 1 and isinstance(args[0], list):
            target[key].extend(deepcopy(args[0]))
        elif (
            kind == "slide"
            and len(args) == 2
            and type(args[0]) is int
            and 0 <= args[0] <= len(target[key])
            and isinstance(args[1], list)
        ):
            target[key] = target[key][args[0] :] + deepcopy(args[1])
        else:
            raise ValueError("存档含有未知效果")
    return state


def _entry(old, state, command, events, previous):
    body = {
        "revision": state["revision"],
        "previous": previous,
        "command": command,
        "events": events,
        "effects": list(_diff(old, state)),
        "state_hash": bal.digest(state),
    }
    return {**body, "checksum": bal.digest(body)}


def _checked_entry(record, state, revision, previous):
    if record["revision"] != revision or record["previous"] != previous:
        raise ValueError("事件的版本链不完整")
    if record["checksum"] != bal.digest(
        {k: v for k, v in record.items() if k != "checksum"}
    ):
        raise ValueError("事件记录的校验和不符")
    sequence = state["sequence"] if state else 0
    prior_minute = state["minute"] if state else 0
    state = _apply(state, record["effects"])
    if state["revision"] != revision or record["state_hash"] != bal.digest(state):
        raise ValueError("回放状态校验不符")
    for event in record["events"]:
        if event.get("schema_version") != "game-event/1" or not event.get("cause"):
            raise ValueError("事件协议或因果引用无效")
        event_protocol.check_event(event["kind"], event["visible"], event.get("data"))
        sequence += 1
        if (
            event["id"] != f"{state['stream']}/e{sequence}"
            or not prior_minute <= event["minute"] <= state["minute"]
        ):
            raise ValueError("事件序号或游戏时刻不符")
        if event["kind"] == "SimulationPolicyChanged" and event["visible"]:
            raise ValueError("控制事件进入了角色日志")
        prior_minute = event["minute"]
    if state["sequence"] != sequence:
        raise ValueError("事件尾序号不符")
    engine.validate(state)
    return state


class GameStore:
    def __init__(self, path):
        self.path = str(path)
        self._keepalive = None
        if self.path == ":memory:":
            self.path = (
                "file:juzhongshi-" + uuid.uuid4().hex + "?mode=memory&cache=shared"
            )
            self._keepalive = sqlite3.connect(
                self.path, uri=True, check_same_thread=False
            )
        else:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2):
                raise GameError("incompatible_save", "该数据库使用了不同的存档版本。")
            if (
                version == 0
                and db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='world_state'"
                ).fetchone()
            ):
                raise GameError(
                    "incompatible_save",
                    "这是早期原型的数据库，请保留原件并为新生涯另选文件。",
                )
            db.execute("PRAGMA journal_mode=WAL")
            if version == 1 and not self._keepalive:
                self.backup(Path(self.path).with_suffix(".schema1-backup.sqlite3"))
            # executescript begins with an explicit transaction. Neither the schema nor
            # the version marker survives an interrupted historical-feed backfill.
            db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA + outbox.SCHEMA)
            if db.execute("PRAGMA user_version").fetchone()[0] == 1:
                for row in db.execute(
                    "SELECT world,value FROM journal ORDER BY world,revision"
                ):
                    outbox.enqueue(db, row["world"], json.loads(row["value"]))
            db.execute("PRAGMA user_version=2")

    @contextmanager
    def _db(self, write=False, snapshot=False):
        db = sqlite3.connect(
            self.path, timeout=20, isolation_level=None, uri=self._keepalive is not None
        )
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            if write:
                db.execute("BEGIN IMMEDIATE")
            elif snapshot:
                db.execute("BEGIN")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _world(db, wid):
        row = db.execute("SELECT * FROM careers WHERE id=?", (wid,)).fetchone()
        if row is None:
            raise GameError("not_found", "未找到这份生涯档案。")
        return row

    @staticmethod
    def _insert_world(db, wid, state, chain):
        db.execute(
            "INSERT INTO careers VALUES(?,?,?,?,?,?,?)",
            (
                wid,
                state["name"],
                state["start"],
                state["minute"],
                state["revision"],
                bal.canonical(state),
                chain,
            ),
        )

    @staticmethod
    def _record(db, wid, record, state):
        db.execute(
            "INSERT INTO journal VALUES(?,?,?)",
            (wid, record["revision"], bal.canonical(record)),
        )
        outbox.enqueue(db, wid, record)
        if record["revision"] % 32 == 0:
            db.execute(
                "INSERT INTO snapshots VALUES(?,?,?)",
                (wid, record["revision"], bal.canonical(state)),
            )

    @staticmethod
    def _update(db, wid, state, chain):
        db.execute(
            "UPDATE careers SET name=?,start=?,minute=?,revision=?,projection=?,chain=? WHERE id=?",
            (
                state["name"],
                state["start"],
                state["minute"],
                state["revision"],
                bal.canonical(state),
                chain,
                wid,
            ),
        )

    def create(self, start="S01", name="新任联络员", balance="0.500000", seed=None):
        wid = uuid.uuid4().hex
        req = checked(
            engine.NewCareer,
            dict(
                start=start,
                name=name,
                balance=balance,
                seed=uuid.uuid4().hex if seed is None else seed,
            ),
        )
        if not req.name.strip():
            raise GameError("invalid_input", "请填写角色称谓。")
        state, events = engine.genesis(wid, req)
        entry = _entry(
            None, state, {"kind": "Genesis", **req.model_dump()}, events, ZERO
        )
        view = engine.player_view(state)
        with self._db(write=True) as db:
            self._insert_world(db, wid, state, entry["checksum"])
            self._record(db, wid, entry, state)
        return view

    def list_worlds(self):
        with self._db() as db:
            rows = db.execute(
                "SELECT id AS world_id,name,start,minute,revision,json_extract(projection,'$.parent') AS ancestry FROM careers ORDER BY rowid DESC"
            )
            result = []
            for row in rows:
                item = dict(row)
                ancestry = item.pop("ancestry")
                item["parent"] = json.loads(ancestry) if ancestry is not None else None
                result.append(item)
            return result

    def history(self, world_id, before=None, limit=50):
        """Page backwards through committed player-visible entries, including old branches."""
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise GameError("invalid_input", "每页可读取 1 至 100 条记录。")
        with self._db(snapshot=True) as db:
            current = self._world(db, world_id)["revision"]
            ceiling, offset = current + 1, 0
            if before is not None:
                import re

                if not isinstance(before, str) or not re.fullmatch(
                    r"[0-9]{1,12}:[0-9]{1,12}", before
                ):
                    raise GameError("invalid_input", "经过页码无效。")
                ceiling, offset = map(int, before.split(":"))
            rows = db.execute(
                "SELECT revision,payload FROM notification_outbox WHERE world=? "
                "AND revision<=? ORDER BY revision DESC",
                (world_id, ceiling),
            )
            events, last = [], None
            for row in rows:
                revision = row["revision"]
                entries = json.loads(row["payload"])["timeline"]
                stop = (
                    min(offset, len(entries)) if revision == ceiling else len(entries)
                )
                for index in range(stop - 1, -1, -1):
                    if len(events) == limit:
                        return {
                            "revision": current,
                            "events": events[::-1],
                            "next": last,
                        }
                    events.append(entries[index])
                    last = f"{revision}:{index}"
            return {"revision": current, "events": events[::-1], "next": None}

    def view(self, world_id):
        with self._db() as db:
            state = json.loads(self._world(db, world_id)["projection"])
        return engine.player_view(state)

    def has_receipt(self, world_id, command_id):
        with self._db() as db:
            return (
                db.execute(
                    "SELECT 1 FROM receipts WHERE world=? AND id=?",
                    (world_id, command_id),
                ).fetchone()
                is not None
            )

    def receipt(self, world_id, command_id):
        with self._db(snapshot=True) as db:
            self._world(db, world_id)
            row = db.execute(
                "SELECT revision FROM receipts WHERE world=? AND id=?",
                (world_id, command_id),
            ).fetchone()
            return {
                "status": "committed" if row else "unknown",
                "revision": row["revision"] if row else None,
                "command_id": command_id,
            }

    def _as_at(self, db, wid, revision):
        snap = db.execute(
            "SELECT revision,value FROM snapshots WHERE world=? AND revision<=? ORDER BY revision DESC LIMIT 1",
            (wid, revision),
        ).fetchone()
        state = None
        first = 0
        if snap is not None:
            try:
                state = json.loads(snap["value"])
            except (ValueError, TypeError):
                state = None
            first = snap["revision"] + 1
            check = db.execute(
                "SELECT value FROM journal WHERE world=? AND revision=?",
                (wid, snap["revision"]),
            ).fetchone()
            if (
                state is None
                or check is None
                or bal.digest(state) != json.loads(check[0])["state_hash"]
            ):
                state = None
                first = 0
        for row in db.execute(
            "SELECT value FROM journal WHERE world=? AND revision>=? AND revision<=? ORDER BY revision",
            (wid, first, revision),
        ):
            state = _apply(state, json.loads(row[0])["effects"])
        if state is None or state["revision"] != revision:
            raise GameError("not_found", "没有找到指定历史版本。")
        return state

    def _prepare_candidates(self, world_id, request, provider):
        if provider is None or request.kind != "advance":
            return {}
        with self._db(snapshot=True) as db:
            row = self._world(db, world_id)
            already = db.execute(
                "SELECT 1 FROM receipts WHERE world=? AND id=?",
                (world_id, request.command_id),
            ).fetchone()
            if already or row["revision"] != request.expected_revision:
                return {}
            state = json.loads(row["projection"])
        menus = {}
        # A dry run collects eligible, knowledge-filtered menus. It cannot commit.
        engine.resolve(state, request, collect=menus)
        proposals = {}
        for menu_hash, menu in menus.items():
            keys, failed = provider.choose(menu)
            if not failed and keys:
                proposals[menu_hash] = {"model": provider.model, "key": keys[0]}
        return proposals

    def execute(
        self, world_id, command_id, expected_revision, kind, args, provider=None
    ):
        req = checked(
            engine.Command,
            dict(
                command_id=command_id,
                expected_revision=expected_revision,
                kind=kind,
                args=args,
            ),
        )
        request = req.model_dump()
        fingerprint = bal.digest(request)
        proposals = self._prepare_candidates(world_id, req, provider)
        with self._db(write=True) as db:
            row = self._world(db, world_id)
            old = db.execute(
                "SELECT request_hash,revision FROM receipts WHERE world=? AND id=?",
                (world_id, command_id),
            ).fetchone()
            if old:
                if fingerprint != old["request_hash"]:
                    raise GameError(
                        "idempotency_conflict", "同一个命令编号已经用于不同的请求。"
                    )
                return engine.player_view(self._as_at(db, world_id, old["revision"]))
            if expected_revision != row["revision"]:
                raise GameError(
                    "revision_conflict", "这份档案已更新，请刷新后重新确认。"
                )
            before = json.loads(row["projection"])
            state, events = engine.resolve(before, req, proposals=proposals)
            if state["revision"] != before["revision"]:
                entry = _entry(before, state, request, events, row["chain"])
                self._record(db, world_id, entry, state)
                self._update(db, world_id, state, entry["checksum"])
            db.execute(
                "INSERT INTO receipts VALUES(?,?,?,?)",
                (world_id, command_id, fingerprint, state["revision"]),
            )
            view = engine.player_view(state)
        return view

    def _history(self, db, wid, upto):
        return [
            json.loads(r[0])
            for r in db.execute(
                "SELECT value FROM journal WHERE world=? AND revision<=? ORDER BY revision",
                (wid, upto),
            )
        ]

    def _export(self, db, wid, upto):
        history = self._history(db, wid, upto)
        receipts = [
            dict(r)
            for r in db.execute(
                "SELECT id,request_hash,revision FROM receipts WHERE world=? AND revision<=? ORDER BY id",
                (wid, upto),
            )
        ]
        state = self._as_at(db, wid, upto)
        parent = state.get("parent") or {}
        meta = {
            **VERSION,
            "world_id": wid,
            "world_revision": upto,
            "last_event_sequence": state["sequence"],
            "snapshot_hash": history[-1]["state_hash"],
            "genesis_seed": history[0]["command"]["seed"],
            "parent_world_id": parent.get("world_id"),
            "fork_revision": parent.get("revision"),
        }
        body = {
            "manifest": meta,
            "world_id": wid,
            "revision": upto,
            "history": history,
            "receipts": receipts,
        }
        return {**body, "checksum": bal.digest(body)}

    def export(self, world_id):
        with self._db(snapshot=True) as db:
            row = self._world(db, world_id)
            return self._export(db, world_id, row["revision"])

    def backup(self, destination):
        """Online Backup API includes committed WAL pages, then atomically replace."""
        import os
        import tempfile

        destination = Path(destination)
        if (
            self._keepalive is None
            and destination.resolve() == Path(self.path).resolve()
        ):
            raise GameError("invalid_input", "备份目标须区别于当前数据库。")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=destination.parent, prefix=".jzs-backup-")
        os.close(fd)
        try:
            with self._db() as source:
                target = sqlite3.connect(name)
                try:
                    source.backup(target)
                    if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise GameError("invalid_save", "备份完整性检查失败。")
                finally:
                    target.close()
            os.replace(name, destination)
        finally:
            Path(name).unlink(missing_ok=True)

    def _verify(self, data):
        try:
            if (
                not isinstance(data, dict)
                or not isinstance(data.get("manifest"), dict)
                or any(data["manifest"].get(k) != v for k, v in VERSION.items())
            ):
                raise GameError(
                    "incompatible_save",
                    "此存档的格式、规则或内容包与当前版本不一致。原档案可以保留。",
                )
            saved = SavedWorld.model_validate(data)
            if saved.checksum != bal.digest(
                {k: v for k, v in data.items() if k != "checksum"}
            ):
                raise ValueError("文件校验和不符")
            state = None
            chain = ZERO
            if len(saved.history) != saved.revision + 1 or len(
                {r.id for r in saved.receipts}
            ) != len(saved.receipts):
                raise ValueError("版本数或收据编号不符")
            for revision, entry in enumerate(data["history"]):
                state = _checked_entry(entry, state, revision, chain)
                chain = entry["checksum"]
            if state["world_id"] != saved.world_id or any(
                r.revision > saved.revision for r in saved.receipts
            ):
                raise ValueError("世界与收据不匹配")
            m = saved.manifest
            parent = state.get("parent") or {}
            if (
                m.world_id != saved.world_id
                or m.world_revision != saved.revision
                or m.last_event_sequence != state["sequence"]
                or m.snapshot_hash != data["history"][-1]["state_hash"]
                or m.genesis_seed != data["history"][0]["command"]["seed"]
                or m.parent_world_id != parent.get("world_id")
                or m.fork_revision != parent.get("revision")
            ):
                raise ValueError("存档清单与回放不一致")
            # Validate the complete player projection before attempting installation.
            engine.player_view(state)
            return state
        except GameError:
            raise
        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            AttributeError,
            OverflowError,
            RecursionError,
        ) as exc:
            raise GameError("invalid_save", "档案未通过完整性检查。") from exc

    def replay(self, world_id):
        with self._db(snapshot=True) as db:
            row = self._world(db, world_id)
            state = self._verify(self._export(db, world_id, row["revision"]))
            return bal.canonical(state) == row["projection"]

    def _install(self, db, wid, data, state):
        self._insert_world(db, wid, state, data["history"][-1]["checksum"])
        current = None
        for record in data["history"]:
            current = _apply(current, record["effects"])
            self._record(db, wid, record, current)
        for r in data["receipts"]:
            db.execute(
                "INSERT INTO receipts VALUES(?,?,?,?)",
                (wid, r["id"], r["request_hash"], r["revision"]),
            )

    def _branch(self, db, data, state):
        wid = uuid.uuid4().hex
        # Persist the unmodified inherited journal; continue in a new namespace.
        # Already bound tasks/thresholds retain their sampled values and IDs.
        self._install(db, wid, {**data, "receipts": []}, state)
        before = deepcopy(state)
        state.update(
            world_id=wid,
            stream=wid,
            revision=state["revision"] + 1,
            rng_seed=bal.digest([state["rng_seed"], "branch", wid]),
            parent={"world_id": data["world_id"], "revision": before["revision"]},
        )
        entry = _entry(
            before,
            state,
            {"kind": "BranchCreated", "parent": state["parent"]},
            [],
            data["history"][-1]["checksum"],
        )
        self._record(db, wid, entry, state)
        self._update(db, wid, state, entry["checksum"])
        return engine.player_view(state)

    def fork(self, world_id, revision):
        if type(revision) is not int or revision < 0:
            raise GameError("invalid_input", "分支版本无效。")
        with self._db(write=True) as db:
            self._world(db, world_id)
            state = self._as_at(db, world_id, revision)
            # Pre-branch ancestors belong to their original world, even if their
            # bytes are also present in the child's history.
            data = self._export(db, world_id, revision)
            return self._branch(db, data, state)

    def restore(self, data):
        state = self._verify(data)
        wid = state["world_id"]
        with self._db(write=True) as db:
            row = db.execute("SELECT * FROM careers WHERE id=?", (wid,)).fetchone()
            if row is None:
                self._install(db, wid, data, state)
            elif row["chain"] != data["history"][-1]["checksum"]:
                # A retried import of a historical save need not create an
                # identical second branch. Once that copy advances, importing
                # again represents a fresh restart at the archived point.
                prior = db.execute(
                    "SELECT c.projection FROM restored_versions i JOIN careers c ON c.id=i.target_world "
                    "WHERE i.source_id=? AND i.archive_hash=? AND c.revision=i.initial_revision",
                    (wid, data["checksum"]),
                ).fetchone()
                if prior is not None:
                    return engine.player_view(json.loads(prior["projection"]))
                branched = self._branch(db, data, state)
                db.execute(
                    "INSERT INTO restored_versions VALUES(?,?,?,?) "
                    "ON CONFLICT(source_id,archive_hash) DO UPDATE SET target_world=excluded.target_world,initial_revision=excluded.initial_revision",
                    (wid, data["checksum"], branched["world_id"], branched["revision"]),
                )
                return branched
            else:
                for receipt in data["receipts"]:
                    old = db.execute(
                        "SELECT request_hash,revision FROM receipts WHERE world=? AND id=?",
                        (wid, receipt["id"]),
                    ).fetchone()
                    if old and (
                        old["request_hash"] != receipt["request_hash"]
                        or old["revision"] != receipt["revision"]
                    ):
                        raise GameError(
                            "history_conflict", "这份存档含有相互冲突的命令收据。"
                        )
                    db.execute(
                        "INSERT OR IGNORE INTO receipts VALUES(?,?,?,?)",
                        (
                            wid,
                            receipt["id"],
                            receipt["request_hash"],
                            receipt["revision"],
                        ),
                    )
        return engine.player_view(state)
