import sqlite3
from contextlib import contextmanager
import pytest
from game import outbox
from game.store import GameStore


def test_delivery_after_worker_crash_and_expired_lease(tmp_path):
    path = tmp_path / "career.sqlite3"
    s = GameStore(path)
    v = s.create(seed="delivery")
    w = v["world_id"]
    rev = outbox.claim(s, w, "worker1", 10, ttl=2)
    assert rev == 0
    other = GameStore(path)
    assert outbox.claim(other, w, "worker2", 11) is None
    assert outbox.claim(other, w, "worker2", 13, ttl=2) == rev
    outbox.apply(s, w, rev, "worker1")
    with s._db() as db:
        assert db.execute("SELECT count(*) FROM visible_feed").fetchone()[0] == 0
    outbox.apply(other, w, rev, "worker2")
    # The durable delivery succeeded; this worker dies before the acknowledgment.
    after_restart = GameStore(path)
    assert outbox.claim(after_restart, w, "worker3", 16) == rev
    outbox.apply(after_restart, w, rev, "worker3")
    outbox.acknowledge(after_restart, w, rev, "worker3")
    events = outbox.updates(s, w, -1)
    assert len(events) == 1 and events[0]["timeline"] == v["timeline"]
    assert not outbox.updates(s, w, 0)
    policy = v["policy"]
    updated = s.execute(
        w,
        "policy",
        0,
        "set_balance",
        {
            "balance": "0.765432",
            "expected_policy_version": policy["version"],
            "parameter_package_hash": policy["parameter_package_hash"],
        },
    )
    assert outbox.updates(s, w, 0) == [
        {"revision": updated["revision"], "timeline": []}
    ]


def test_schema_migration_rebuilds_feed_and_protects_original(tmp_path):
    path = tmp_path / "work.sqlite3"
    s = GameStore(path)
    v = s.create(seed="import")
    w = v["world_id"]
    s.execute(w, "c", 0, "compare", {})
    with s._db(write=True) as db:
        db.execute("DROP TABLE visible_feed")
        db.execute("DROP TABLE notification_outbox")
        db.execute("PRAGMA user_version=1")
    s = GameStore(path)
    with sqlite3.connect(path.with_suffix(".schema1-backup.sqlite3")) as old:
        assert old.execute("PRAGMA user_version").fetchone()[0] == 1
        assert old.execute("SELECT revision FROM careers").fetchone()[0] == 1
    assert [m["revision"] for m in outbox.updates(s, w, -1)] == [0, 1]
    assert s.replay(w)


class InjectedFailure(Exception):
    pass


def test_every_sql_write_position_rolls_back(tmp_path, monkeypatch):
    # Includes periodic snapshot, outbox, journal, projection and receipt writes.
    s = GameStore(tmp_path / "fault.sqlite3")
    v = s.create(seed="cut")
    w = v["world_id"]
    for i in range(31):
        s.execute(w, f"day-{i}", i, "advance", {"minutes": 1})
    original = s.export(w)
    connect = s._db
    executed = []
    cutoff = None

    @contextmanager
    def instrumented(write=False, snapshot=False):
        with connect(write=write, snapshot=snapshot) as db:

            class Connection:
                def __getattr__(self, k):
                    return getattr(db, k)

                def execute(self, sql, parameters=()):
                    result = db.execute(sql, parameters)
                    if write and sql.split()[0] in {"INSERT", "UPDATE", "DELETE"}:
                        executed.append(sql)
                        if len(executed) == cutoff:
                            raise InjectedFailure
                    return result

            yield Connection()

    monkeypatch.setattr(s, "_db", instrumented)
    for step in range(1, 12):
        cutoff = step
        executed.clear()
        try:
            v = s.execute(w, "edge", 31, "compare", {})
        except InjectedFailure:
            assert s.export(w) == original and not s.has_receipt(w, "edge")
            with connect() as db:
                assert (
                    db.execute(
                        "SELECT count(*) FROM notification_outbox WHERE revision=32"
                    ).fetchone()[0]
                    == 0
                )
        else:
            assert len(executed) == step - 1
            assert {
                "journal",
                "snapshots",
                "careers",
                "notification_outbox",
                "receipts",
            } <= {
                sql.split()[2].split("(")[0]
                if sql.startswith("INSERT")
                else sql.split()[1]
                for sql in executed
            }
            break
    else:
        pytest.fail("failed to reach deposit boundary")
    assert v["revision"] == 32 and s.replay(w)
