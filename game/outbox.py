"""Durable delivery of authorized PlayerView changes from the game transaction to SSE readers."""

from __future__ import annotations

import json
import time
import uuid
from .balance import canonical

SCHEMA = """
CREATE TABLE IF NOT EXISTS notification_outbox(
    world TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
    owner TEXT, lease_until REAL, delivered INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(world,revision), FOREIGN KEY(world,revision) REFERENCES journal(world,revision)
);
CREATE INDEX IF NOT EXISTS pending_notifications ON notification_outbox(world,delivered,revision);
CREATE TABLE IF NOT EXISTS visible_feed(
    world TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
    PRIMARY KEY(world,revision), FOREIGN KEY(world,revision) REFERENCES notification_outbox(world,revision)
);
"""


def enqueue(db, world, record):
    fields = ("id", "kind", "minute", "title", "text", "actor", "refs")
    events = [
        {f: event[f] for f in fields} for event in record["events"] if event["visible"]
    ]
    rev = record["revision"]
    db.execute(
        "INSERT INTO notification_outbox(world, revision, payload) VALUES(?,?,?)",
        (world, rev, canonical({"revision": rev, "timeline": events})),
    )


def claim(store, world, worker, now, ttl=15):
    """Only the oldest outstanding batch may be claimed; a cursor cannot skip over a leased gap."""
    with store._db(write=True) as db:
        row = db.execute(
            "SELECT revision,owner,lease_until FROM notification_outbox WHERE world=? AND delivered=0 "
            "ORDER BY revision LIMIT 1",
            (world,),
        ).fetchone()
        if row is None or (row["owner"] and row["lease_until"] > now):
            return None
        db.execute(
            "UPDATE notification_outbox SET owner=?,lease_until=? WHERE world=? AND revision=?",
            (worker, now + ttl, world, row["revision"]),
        )
        return row["revision"]


def apply(store, world, revision, worker):
    """Write the dispatch effect durably before acknowledging. Re-application has the same key."""
    with store._db(write=True) as db:
        db.execute(
            "INSERT OR IGNORE INTO visible_feed(world,revision,payload) SELECT world,revision,payload "
            "FROM notification_outbox WHERE world=? AND revision=? AND owner=? AND delivered=0",
            (world, revision, worker),
        )


def acknowledge(store, world, revision, worker):
    with store._db(write=True) as db:
        db.execute(
            "UPDATE notification_outbox SET delivered=1,owner=NULL,lease_until=NULL "
            "WHERE world=? AND revision=? AND owner=? AND EXISTS "
            "(SELECT 1 FROM visible_feed WHERE world=? AND revision=?)",
            (world, revision, worker, world, revision),
        )


def updates(store, world, after, limit=64):
    worker = uuid.uuid4().hex
    with store._db() as db:
        store._world(db, world)
        pending = db.execute(
            "SELECT 1 FROM notification_outbox WHERE world=? AND delivered=0 LIMIT 1",
            (world,),
        ).fetchone()
    if pending:
        for _ in range(limit):
            rev = claim(store, world, worker, time.time())
            if rev is None:
                break
            apply(store, world, rev, worker)
            acknowledge(store, world, rev, worker)
    with store._db() as db:
        rows = db.execute(
            "SELECT payload FROM visible_feed WHERE world=? AND revision>? ORDER BY revision LIMIT ?",
            (world, after, limit),
        )
        return [json.loads(row["payload"]) for row in rows]
