"""Read a verified game snapshot in an isolated development workspace.

Examples:
    .venv/bin/python scripts/inspect_game.py view
    .venv/bin/python scripts/inspect_game.py actor --save career.json --actor N09
    .venv/bin/python scripts/inspect_game.py chain --db career.db --world WORLD --revision 8

The shipped application never imports this module. With no source, use a temporary
sample career. Reading a supplied SQLite file uses a read-only connection and the
SQLite Online Backup API, including committed WAL content.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from game import engine
from game.store import GameStore


class SnapshotInspector:
    """Read-only development surface over an already isolated SQLite copy."""

    def __init__(self, isolated_store):
        self._store=isolated_store

    def worlds(self):
        return self._store.list_worlds()

    def inspect(self, section, *, world_id=None, revision=None, actor=None, limit=20):
        if section=="worlds":
            return self.worlds()
        if world_id is None:
            worlds=self.worlds()
            if len(worlds)!=1:
                raise ValueError("请先用 worlds 查看档案，再以 --world 选择。")
            world_id=worlds[0]["world_id"]
        if type(limit) is not int or not 1<=limit<=1000:
            raise ValueError("--limit 范围是 1 至 1000。")
        with self._store._db(snapshot=True) as db:
            row=self._store._world(db,world_id)
            revision=row["revision"] if revision is None else revision
            if type(revision) is not int or not 0<=revision<=row["revision"]:
                raise ValueError("请求的世界版本不存在。")
            archive=self._store._export(db,world_id,revision)
            # A child's earliest records can belong to the source world. Verify
            # that inherited prefix with its recorded identity, not a new ID.
            recorded_state=self._store._as_at(db,world_id,revision)
            if recorded_state["world_id"]!=world_id:
                raise ValueError("该版本属于分支建立以前的父世界，请选择父档案。")
            state=self._store._verify(archive)
        if section=="view":
            return engine.player_view(state)
        if section=="actor":
            if actor not in state["domain"]["actors"]:
                raise ValueError("请用 --actor 指定此档案中的 NPC 编号。")
            record=state["domain"]["actors"][actor]
            return {"world_id":world_id,"revision":revision,"actor":actor,
                    "beliefs":record["beliefs"],"goals":record["goals"],"resources":record["resources"],
                    "plans":record["plans"],"relations":record["relations"],"last_acted":record["last_acted"]}
        if section=="chain":
            events=[event for entry in archive["history"] for event in entry["events"]]
            return {"world_id":world_id,"revision":revision,"valid":True,
                    "events":len(events),"hash":archive["history"][-1]["checksum"],
                    "snapshot_hash":archive["manifest"]["snapshot_hash"],"tail":events[-limit:]}
        if section=="queue":
            tasks=sorted(state["queue"],key=lambda t:(t["due"],t["priority"],t["order"]))
            return {"minute":state["minute"],"total":len(tasks),"tasks":tasks[:limit],
                    "opportunity_clocks":state["clocks"]}
        if section=="quarantine":
            quarantined=state.get("quarantine",[])
            return {"total":len(quarantined),"tasks":quarantined[-limit:]}
        raise ValueError("未知检查类型。")


@contextmanager
def open_snapshot(*, archive=None, database=None):
    if archive is not None and database is not None:
        raise ValueError("请指定一份输入档案。")
    with tempfile.TemporaryDirectory(prefix="jzs-inspect-") as tmp:
        target=Path(tmp)/"isolated.sqlite3"
        if database is not None:
            source_path=Path(database).resolve(strict=True)
            source=sqlite3.connect(source_path.as_uri()+"?mode=ro",uri=True)
            destination=sqlite3.connect(target)
            try:
                source.execute("PRAGMA query_only=ON")
                source.backup(destination)
            finally:
                destination.close()
                source.close()
        store=GameStore(target)
        if archive is not None:
            store.restore(json.loads(Path(archive).read_text(encoding="utf-8")))
        elif database is None:
            viewer=store.create(start="S01",name="示例联络员",seed="inspection-fixture")
            store.execute(viewer["world_id"],"fixture-arrange",0,"advance",{"minutes":180})
        yield SnapshotInspector(store)


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("section",choices=("worlds","view","actor","chain","queue","quarantine"))
    source=parser.add_mutually_exclusive_group()
    source.add_argument("--save",type=Path,help="完整的 JSON 导出")
    source.add_argument("--db",type=Path,help="以只读方式打开 SQLite，然后检查隔离副本")
    parser.add_argument("--world")
    parser.add_argument("--revision",type=int)
    parser.add_argument("--actor")
    parser.add_argument("--limit",type=int,default=20)
    args=parser.parse_args()
    try:
        with open_snapshot(archive=args.save,database=args.db) as inspector:
            result=inspector.inspect(args.section,world_id=args.world,revision=args.revision,
                                     actor=args.actor,limit=args.limit)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,sqlite3.DatabaseError) as exc:
        parser.exit(2,f"检查未完成。{exc}\n")


if __name__=="__main__":
    main()
