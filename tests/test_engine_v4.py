"""Numerical and transactional regression tests for the continuous engine."""

import json
import math
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import game
from game import balance as b, engine as e
from game.store import GameStore

ROOT = Path(__file__).resolve().parents[1]


def test_v4_t01_t03_1001_points_and_neighbours():
    previous = None
    for i in range(1001):
        values = b.parameters(i / 1000)
        numbers = [v for k, v in values.items() if k != "objective_weights"]
        assert all(math.isfinite(x) and x > 0 for x in numbers)
        assert math.isclose(sum(values["objective_weights"]), 1.0)
        if previous:
            assert 0 < previous["admin"] - values["admin"] < 0.001
            assert 0 < values["repair_rate"] - previous["repair_rate"] < 0.002
        previous = values
    assert 450 * (
        b.parameters(0.499)["admin"] - b.parameters(0.501)["admin"]
    ) == pytest.approx(0.585)


@pytest.mark.parametrize(
    "value",
    [
        None,
        False,
        True,
        "",
        " 0.500000",
        "0.5",
        0.5,
        "1.000001",
        "NaN",
        "Infinity",
        "0.000000\n",
    ],
)
def test_v4_t02_strict_target(value):
    with pytest.raises(e.GameError):
        e.checked(
            b.PolicySetting,
            {
                "balance": value,
                "expected_policy_version": 1,
                "parameter_package_hash": b.PACKAGE_HASH,
            },
        )


def test_v4_t04_t05_t08_official_golden():
    fixture = json.loads((ROOT / "BALANCE_GOLDEN_VALUES.json").read_text())
    for row in fixture["vectors"]:
        n = float(row["requested_balance"])
        values = b.parameters(n)
        for k, spec in row["parameters"].items():
            if k != "balance_eff":
                assert values[k] == pytest.approx(spec)
        m = row["fixed_state"]
        raw = 30 + 450 * values["admin"]
        msg = 15 + 225 * values["message_queue"]
        assert raw == pytest.approx(m["admin_duration_raw"])
        assert math.ceil(raw) == m["admin_duration_ceil"]
        assert msg == pytest.approx(m["message_duration_raw"])
        assert math.ceil(msg) == m["message_duration_ceil"]
        assert b.counteroffer(0.35, n) == pytest.approx(m["counteroffer_probability"])
        assert b.counteroffer(0, n) == 0 and b.counteroffer(1, n) == 1
        scores = {"negotiate": (0.4, 0.9), "none": (0.3, 0.4), "routine": (0.9, 0.3)}
        probabilities = b.distribution(scores, n)
        assert list(probabilities) == sorted(scores)
        assert sum(probabilities.values()) == pytest.approx(1)
        for candidate in row["candidate_distribution"]:
            assert probabilities[candidate["candidate_id"]] == pytest.approx(
                candidate["probability"]
            )
    assert b.distribution({"none": (0, 0), "ask": (0, 0)}, 0.37) == {
        "none": 0.5,
        "ask": 0.5,
    }
    with pytest.raises(ValueError):
        b.distribution({"ask": (0, 0)}, 0.5)
    assert e.work_elapsed(4 * 1440 + 7 * 60, 120) == (
        2 * 1440 + 16 * 60 + 120
    )  # Friday 16:00 -> Monday 10:00


def test_v4_t06_t07_ramp_quadrature():
    p = {"minute": 0, "start": 0.5, "target": "1.000000", "version": 2}
    assert [b.effective(p, t) for t in (0, 60, 120, 180, 240)] == [
        0.5,
        0.578125,
        0.75,
        0.921875,
        1.0,
    ]
    assert b.integral(p, 0, 120) == pytest.approx(71.25)
    assert b.integral(p, 0, 240) == pytest.approx(180)
    assert b.delta_hazard(p, 0, 240, "verification_rate", 0.1 / 60) == pytest.approx(
        0.64
    )
    for left, right in [(0, 1), (39, 159), (120, 279), (225, 480)]:
        areas = [
            b.effective(p, left + (i + 0.5) * (right - left) / 1000)
            for i in range(1000)
        ]
        assert b.integral(p, left, right) == pytest.approx(
            math.fsum(areas) * (right - left) / 1000, abs=2e-5
        )
    assert b.integral(p, 0, 400) == pytest.approx(
        sum(b.integral(p, x, x + 1) for x in range(400))
    )


# The tiny domain below isolates actual scheduler/SQLite failures from changing
# narrative content; release journey tests exercise the real domain separately.
def _act(d, kind, args, ctx):
    if kind == "request":
        ctx.schedule("arrive", {}, ctx.duration("admin", 30, 450), title="查证")
        ctx.emit("已预约")
    elif kind == "short":
        ctx.schedule("attention", {}, args["delay"], decision=True, title="听证")
    elif kind == "resume":
        d["pending"] = False
    elif kind == "fault":
        d["incorrect"] = 1
        ctx.emit("未提交")
        raise ValueError("失败回滚")
    elif kind == "eligible":
        d["on"] = args["on"]
    else:
        raise ValueError("不可执行")


def _complete(d, kind, args, ctx):
    if kind == "attention":
        d["pending"] = True
    ctx.emit(kind, title=kind)


@pytest.fixture
def tiny(monkeypatch):
    module = SimpleNamespace(
        genesis=lambda s, n, seed: {"on": True, "count": 0, "pending": False},
        init=lambda d, c: None,
        project=lambda d: {"count": d["count"]},
        act=_act,
        complete=_complete,
        quarter=lambda d, q, c: c.emit(str(q), kind="Quarter"),
        decision_pending=lambda d: d["pending"],
        eligible=lambda d, p: d["on"] and p == "verification",
        opportunity=lambda d, p, c: d.update(count=d["count"] + 1),
    )
    monkeypatch.setattr(game, "world", module, raising=False)
    return module


def _policy(v, target):
    return {
        "balance": target,
        "parameter_package_hash": b.PACKAGE_HASH,
        "expected_policy_version": v["policy"]["version"],
    }


def test_v4_t16_t18_t20_t21_t23_committed_policy_and_resume(tiny, tmp_path):
    s = GameStore(tmp_path / "game.db")
    v = s.create(seed="hold")
    w = v["world_id"]
    v = s.execute(w, "request", 0, "request", {})
    due = v["appointments"][0]["due"]
    v = s.execute(w, "change", 1, "set_balance", _policy(v, "1.000000"))
    v = s.execute(w, "step", 2, "advance", {"minutes": 61})
    old = v["policy"]["effective"]
    v = s.execute(w, "reanchor", 3, "set_balance", _policy(v, "0.131217"))
    assert v["policy"]["effective"] == old
    assert v["appointments"][0]["due"] == due
    assert s.view(w) == v
    assert not any(
        event["kind"] == "SimulationPolicyChanged" for event in v["timeline"]
    )
    snapshot = s.export(w)
    assert (
        sum(
            event["kind"] == "SimulationPolicyChanged"
            for r in snapshot["history"]
            for event in r["events"]
        )
        == 2
    )
    other = GameStore(tmp_path / "new.db")
    assert other.restore(snapshot) == v
    assert other.replay(w)
    args = _policy(v, "0.131217")
    assert other.execute(w, "same", 4, "set_balance", args) == v
    with pytest.raises(e.GameError, match="刷新"):
        other.execute(w, "old-confirmation", 3, "request", {})
    assert other.execute(w, "step-more", 4, "advance", {"minutes": 40}) == s.execute(
        w, "step-more", 4, "advance", {"minutes": 40}
    )


def test_v4_t17_atomicity_concurrency_idempotence(tiny, tmp_path):
    s = GameStore(tmp_path / "same.db")
    w = s.create(seed="parallel")["world_id"]
    before = s.export(w)
    with pytest.raises(e.GameError):
        s.execute(w, "fault", 0, "fault", {})
    assert s.export(w) == before
    barrier = threading.Barrier(2)

    def concurrent(cid):
        barrier.wait()
        try:
            return s.execute(w, cid, 0, "request", {})["revision"]
        except e.GameError as err:
            return err.code

    with ThreadPoolExecutor(2) as pool:
        assert sorted([str(x) for x in pool.map(concurrent, ["one", "two"])]) == [
            "1",
            "revision_conflict",
        ]
    first = s.export(w)["receipts"][0]["id"]
    receipt = s.view(w)
    s.execute(w, "next", 1, "advance", {"minutes": 20})
    assert s.execute(w, first, 0, "request", {}) == receipt
    with pytest.raises(e.GameError, match="不同的请求"):
        s.execute(w, first, 2, "advance", {"minutes": 20})
    # A storage exception after the journal update leaves no partial revision.
    with sqlite3.connect(tmp_path / "same.db") as db:
        db.execute(
            "CREATE TRIGGER fail_test BEFORE INSERT ON receipts BEGIN SELECT RAISE(ABORT,'test failure'); END"
        )
    prev = s.export(w)
    with pytest.raises(sqlite3.IntegrityError):
        s.execute(w, "disk", 2, "request", {})
    assert s.export(w) == prev


def test_v4_t19_t22_opportunity_and_pause(tiny, tmp_path):
    s = GameStore(tmp_path / "main.db")
    v = s.create(seed="common-clock")
    w = v["world_id"]
    before = s.export(w)
    other = GameStore(tmp_path / "other.db")
    other.restore(before)
    v = s.execute(w, "big", 0, "advance", {"minutes": 10000})
    for i in range(20):
        vb = other.execute(w, f"step{i}", i, "advance", {"minutes": 500})
    assert v["count"] == vb["count"] > 0
    with s._db() as db1, other._db() as db2:
        a = json.loads(s._world(db1, w)["projection"])
        c = json.loads(other._world(db2, w)["projection"])
        assert a["clocks"] == c["clocks"]
    ctx = e.Context(a)
    name = "verification"
    assert not e._fire(a, ctx, name, a["clocks"][name]["generation"] - 1)
    h = a["clocks"][name]["H"]
    s.execute(w, "off", 1, "eligible", {"on": False})
    s.execute(w, "still", 2, "advance", {"minutes": 7000})
    with s._db() as db:
        assert json.loads(s._world(db, w)["projection"])["clocks"][name]["H"] == h
    v = s.execute(w, "meeting", 3, "short", {"delay": 15})
    v = s.execute(w, "approach", 4, "advance", {"minutes": 200})
    assert v["minute"] == 17015
    with pytest.raises(e.GameError):
        s.execute(w, "skip", 5, "advance", {"minutes": 50})
    with pytest.raises(e.GameError):
        s.execute(w, "control", 5, "set_balance", _policy(v, "0.400000"))


def test_integrity_branch_replay_and_wal_backup(tiny, tmp_path):
    s = GameStore(tmp_path / "原 存档.db")
    a = s.create(seed="branch")
    w = a["world_id"]
    s.execute(w, "first", 0, "request", {})
    old = s.export(w)
    s.execute(w, "wait", 1, "advance", {"minutes": 1})
    assert s.replay(w)
    fork = s.restore(old)
    assert (
        fork["world_id"] != w
        and s.view(w)["minute"] == 1
        and s.replay(fork["world_id"])
    )
    assert s.restore(old) == fork
    matching = [
        item for item in s.list_worlds() if item["world_id"] == fork["world_id"]
    ]
    assert matching[0]["parent"] == {"world_id": w, "revision": 1}
    fork2 = s.fork(w, 0)
    assert len(s.list_worlds()) == 3 and fork2["minute"] == 0
    s.execute(fork2["world_id"], "first", fork2["revision"], "request", {})
    assert s.replay(fork2["world_id"])
    corrupted = deepcopy(s.export(w))
    corrupted["history"][0]["events"][0]["text"] = "篡改"
    with pytest.raises(e.GameError):
        s.restore(corrupted)
    assert len(s.list_worlds()) == 3
    s.backup(tmp_path / "新 备份.db")
    copy = GameStore(tmp_path / "新 备份.db")
    assert copy.view(w) == s.view(w) and copy.replay(w)
    with sqlite3.connect(tmp_path / "原 存档.db") as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM journal")


def test_disk_full_rolls_back_and_backup_replace_is_atomic(tiny, tmp_path, monkeypatch):
    from contextlib import contextmanager

    store = GameStore(tmp_path / "career.db")
    view = store.create(seed="storage-fault")
    wid = view["world_id"]
    baseline = store.export(wid)
    ordinary_db = store._db

    @contextmanager
    def constrained(*args, **kwargs):
        with ordinary_db(*args, **kwargs) as db:
            pages = db.execute("PRAGMA page_count").fetchone()[0]
            db.execute(f"PRAGMA max_page_count={pages}")
            yield db

    def big(d, kind, args, ctx):
        d["archive"] = "大" * 200_000
        ctx.emit("存储测试")

    with patch.object(store, "_db", constrained), patch.object(tiny, "act", big):
        with pytest.raises(sqlite3.OperationalError) as failure:
            store.execute(wid, "atomic", 0, "expand", {})
    assert failure.value.sqlite_errorname == "SQLITE_FULL"
    assert store.export(wid) == baseline
    output = tmp_path / "backup.db"
    store.backup(output)
    prior = output.read_bytes()
    with patch("os.replace", side_effect=OSError("模拟导出安装中断")):
        with pytest.raises(OSError):
            store.backup(output)
    assert output.read_bytes() == prior


def test_missing_and_damaged_checkpoints_fall_back(tiny, tmp_path):
    store = GameStore(tmp_path / "recovery.db")
    wid = store.create(seed="snapshots")["world_id"]
    for i in range(33):
        store.execute(wid, f"move-{i}", i, "advance", {"minutes": 1})
    with sqlite3.connect(tmp_path / "recovery.db") as db:
        db.execute("UPDATE snapshots SET value='{}' WHERE revision=32")
    branch = store.fork(wid, 32)
    assert branch["minute"] == 32 and store.replay(branch["world_id"])
    with sqlite3.connect(tmp_path / "recovery.db") as db:
        db.execute("DELETE FROM snapshots")
    assert store.fork(wid, 30)["minute"] == 30
    assert store.replay(wid)


def test_unsupported_legacy_database_is_untouched(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE world_state(id INTEGER PRIMARY KEY,projection TEXT)")
        db.execute("INSERT INTO world_state VALUES (1,'legacy fact')")
    old = path.read_bytes()
    with pytest.raises(e.GameError) as failure:
        GameStore(path)
    assert failure.value.code == "incompatible_save" and path.read_bytes() == old


def test_same_minute_policy_changes_keep_thresholds_and_existing_tasks(tiny, tmp_path):
    s = GameStore(tmp_path / "reanchor.db")
    v = s.create(seed="clock-policy")
    wid = v["world_id"]
    v = s.execute(wid, "admit", 0, "request", {})
    v = s.execute(wid, "first-minute", 1, "advance", {"minutes": 19})

    def inspect():
        with s._db() as db:
            return json.loads(s._world(db, wid)["projection"])

    original = inspect()
    for i, target in enumerate(["0.230119", "0.000000", "1.000000", "0.501001"]):
        v = s.execute(
            wid, f"control-{i}", v["revision"], "set_balance", _policy(v, target)
        )
    after = inspect()
    assert after["queue"] == original["queue"]
    for name in e.PROCESSES:
        old = original["clocks"][name]
        new = after["clocks"][name]
        assert (new["H"], new["E"], new["slot"], new["episode"]) == (
            old["H"],
            old["E"],
            old["slot"],
            old["episode"],
        )
        assert new["generation"] > old["generation"]
    assert v["policy"]["effective"] == 0.5
    assert [r["target"] for r in v["policy"]["trajectory"]] == [
        "0.500000",
        "0.230119",
        "0.000000",
        "1.000000",
        "0.501001",
    ]
    assert not any("policy" in record for record in v["timeline"])
    assert s.replay(wid)


def test_no_state_change_or_parallel_double_application_for_same_id(tiny, tmp_path):
    s = GameStore(tmp_path / "retry.db")
    wid = s.create(seed="same-id")["world_id"]
    barrier = threading.Barrier(3)

    def attempt(_):
        barrier.wait()
        return s.execute(wid, "pending", 0, "request", {})

    with ThreadPoolExecutor(3) as pool:
        a, bview, c = pool.map(attempt, range(3))
    assert a == bview == c and len(a["appointments"]) == 1
    assert len(s.export(wid)["history"]) == 2
