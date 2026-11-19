"""Read-only audit of actual commits. Negative probes use the same public command gateway."""

from collections import Counter
import json
from game import balance, engine
from game.catalog import WAN
from game.store import ZERO

# These tests cover boundaries a projection inspection alone cannot establish.
INVARIANTS = {
    "INV-01": (
        "每次命令的收据、日志和状态哈希一致",
        "test_disk_full_rolls_back_and_backup_replace_is_atomic；test_bounded_advisor_transport_and_fallback",
    ),
    "INV-02": (
        "日志连续、哈希前驱一致，事件 ID 和分钟有序",
        "test_integrity_branch_replay_and_wal_backup",
    ),
    "INV-03": (
        "逐命令原请求重交，验证返回相同且写入数不变",
        "test_v4_t17_atomicity_concurrency_idempotence",
    ),
    "INV-04": (
        "每个信念引用该角色先验或已提交事件",
        "test_invitation_refusal_and_actual_arrival_have_separate_witnesses；test_sourced_notes_arrive_in_custody_then_receive_partial_corroboration",
    ),
    "INV-05": (
        "PlayerView 键和时间线均通过可见性检查，失去本子时无原文",
        "test_bounded_advisor_transport_and_fallback；test_notebook_private_and_clocked_exposure",
    ),
    "INV-06": (
        "时钟单调、队列不残留过期任务，已提交事件不早于前一版本",
        "test_v4_t19_t22_opportunity_and_pause",
    ),
    "INV-07": (
        "年度和季度额度、预留、工作组、薪酬和物品来源有效",
        "test_conditional_budget_and_real_work；test_role_grant_lease_and_reject_forgery",
    ),
    "INV-08": (
        "实际案卷、材料、岗位认定与终局引用属于已提交事件",
        "test_acquired_evidence_and_formal_ending；test_all_cases_can_receive_new_material_after_three_quarters",
    ),
    "INV-09": (
        "无权开放的请求遭拒，验证三张表没有副作用",
        "test_conditional_budget_and_real_work；test_role_grant_lease_and_reject_forgery",
    ),
    "INV-10": (
        "实际抽样槽、样本、权重、规则包及封存结果可复算",
        "test_integrity_branch_replay_and_wal_backup；test_same_minute_policy_changes_keep_thresholds_and_existing_tasks",
    ),
    "INV-11": (
        "无检查和授权的开放无法提交；已开放设施均有批准",
        "test_service_and_accessible_evidence_with_divergent_paths；test_late_career_retirement_care_and_health_records",
    ),
    "INV-12": (
        "核对待处理任务的唯一 ID、派生根、同分钟深度和有界扇出",
        "test_scheduler_contains_same_minute_cycles_and_keeps_task",
    ),
}

PRIVATE_KEYS = {
    "rng_seed",
    "variant",
    "actors",
    "beliefs",
    "belief_topics",
    "decision_key",
    "sample",
    "candidate_hash",
    "health_profile",
    "parameter_binding",
    "clock_threshold",
    "queue",
    "witness_ref",
    "vacate_quarter",
    "career",
    "slot",
    "medical_course",
}


def field_names(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from field_names(v)
    elif isinstance(x, list):
        for v in x:
            yield from field_names(v)


class WorldAudit:
    def __init__(self):
        self.counts = Counter()
        self.events = {}
        self.last_minute = 0
        self.previous_hash = ZERO
        self.variant = None

    def inspect(self, run, request=None):
        with run.store._db(snapshot=True) as db:
            rec = run.store._world(db, run.w)
            state = json.loads(rec["projection"])
            latest = json.loads(
                db.execute(
                    "SELECT value FROM journal WHERE world=? AND revision=?",
                    (run.w, rec["revision"]),
                ).fetchone()[0]
            )
            journal_count = db.execute(
                "SELECT COUNT(*) FROM journal WHERE world=?", (run.w,)
            ).fetchone()[0]
            receipt_count = db.execute(
                "SELECT COUNT(*) FROM receipts WHERE world=?", (run.w,)
            ).fetchone()[0]
            if request:
                receipt = db.execute(
                    "SELECT request_hash,revision FROM receipts WHERE world=? AND id=?",
                    (run.w, request["command_id"]),
                ).fetchone()
                assert (
                    receipt
                    and receipt["request_hash"] == balance.digest(request)
                    and receipt["revision"] == state["revision"]
                ), "INV-01"
                assert latest["command"] == request, "INV-01"
            assert (
                latest["state_hash"] == balance.digest(state)
                and latest["checksum"] == rec["chain"]
            ), "INV-01"
        self.counts["INV-01"] += 1
        assert latest["previous"] == self.previous_hash and len(self.events) == state[
            "sequence"
        ] - len(latest["events"]), "INV-02"
        assert latest["revision"] == state["revision"] == journal_count - 1, "INV-02"
        minute = self.last_minute
        for ev in latest["events"]:
            assert (
                ev["id"] == f"{state['stream']}/e{len(self.events) + 1}"
                and minute <= ev["minute"] <= state["minute"]
            ), "INV-02/06"
            assert ev["cause"] and all(x in self.events for x in ev["refs"]), "INV-08"
            self.events[ev["id"]] = ev
            minute = ev["minute"]
            if ev["kind"] == "ChoiceSealed":
                x = ev["data"]
                weights = x["weights"]
                assert (
                    x["slot"]
                    and x["binding"]["parameter_package_hash"] == balance.PACKAGE_HASH
                ), "INV-10"
                assert x["candidate_hash"] == balance.digest(weights) and x[
                    "sample"
                ] == balance.uniform(state["rng_seed"], x["slot"]), "INV-10"
                assert x["outcome"] == balance.pick(weights, x["sample"]), "INV-10"
                self.counts["INV-10"] += 1
        self.previous_hash = latest["checksum"]
        self.counts["INV-02"] += 1
        if request:
            same = run.store.execute(
                run.w,
                request["command_id"],
                request["expected_revision"],
                request["kind"],
                request["args"],
            )
            assert same == run.v and self.marks(run) == (
                state["revision"],
                journal_count,
                receipt_count,
                rec["chain"],
            ), "INV-03"
            self.counts["INV-03"] += 1
        d = state["domain"]
        v = run.v
        for who, a in d["actors"].items():
            assert all(
                ref == f"genesis/{who}" or ref in self.events for ref in a["beliefs"]
            ), "INV-04"
            assert all(
                ref in a["beliefs"] for ref in a.get("belief_topics", {}).values()
            ), "INV-04"
        self.counts["INV-04"] += 1
        assert PRIVATE_KEYS.isdisjoint(field_names(v)), "INV-05"
        assert all(self.events[e["id"]]["visible"] for e in v["timeline"]), "INV-05"
        assert [x["id"] for x in v["appointments"]] == [
            t["id"]
            for t in sorted(
                state["queue"], key=lambda t: (t["due"], t["priority"], t["order"])
            )
            if t["visible"]
        ], "INV-05"
        if not v["notebook"]["accessible"]:
            assert not v["notebook"]["entries"], "INV-05"
        self.counts["INV-05"] += 1
        assert state["minute"] >= self.last_minute and all(
            t["due"] >= state["minute"] for t in state["queue"]
        ), "INV-06"
        self.last_minute = state["minute"]
        self.counts["INV-06"] += 1
        f = d["fiscal"]
        pay = d["payroll"]
        assert (
            0 <= f["annual_left"] <= 8000 * WAN
            and 0 <= f["quarter_used"] <= 2000 * WAN
            and all(n > 0 for n in f["groups"].values())
        ), "INV-07"
        assert (
            sum(f["groups"].values()) <= 12
            and 0 <= pay["paid"] <= pay["authorized"]
            and d["family"]["savings"] >= 0
        ), "INV-07"
        assert f["reserved"] == sum(
            p["allocation"]
            for p in d["projects"].values()
            if p["phase"] == "预留待进场"
        ), "INV-07"
        for doc in d["docs"].values():
            assert (
                doc["version"]
                and doc["refs"]
                and all(ref in self.events for ref in doc["refs"])
            ), "INV-07/08"
        self.counts["INV-07"] += 1
        for row in d["cases"].values():
            assert row["history"] and all(
                edge["ref"] in self.events for edge in row["history"]
            ), "INV-08"
        assert all(r["ref"] in self.events for r in d["investigation"]["findings"]), (
            "INV-08"
        )
        if d["ending"]:
            assert d["ending"]["refs"] and all(
                x in self.events for x in d["ending"]["refs"]
            ), "INV-08"
        self.counts["INV-08"] += 1
        if self.variant is None:
            self.variant = d["variant"]
        assert self.variant == d["variant"], "INV-11"
        if d["passage"]["opened"]:
            assert (
                d["passage"]["approval_ref"] in self.events
                and d["passage"]["check_ref"] in self.events
            ), "INV-11"
        assert all(
            not p["opened"] or bool(p["approvals"] or p["stage_history"])
            for p in d["projects"].values()
        ), "INV-11"
        self.counts["INV-11"] += 1
        ids = set()
        fanout = Counter()
        for task in state["queue"]:
            chain = task["lineage"]
            assert (
                task["id"] not in ids
                and chain["root"]
                and chain["parent"]
                and 0 <= chain["same_minute"] <= 16
            ), "INV-12"
            ids.add(task["id"])
            if chain["same_minute"] > 0:
                fanout[(chain["root"], task["due"])] += 1
        assert all(n <= 128 for n in fanout.values()), "INV-12"
        self.counts["INV-12"] += 1

    @staticmethod
    def marks(run):
        with run.store._db(snapshot=True) as db:
            w = run.store._world(db, run.w)
            return (
                w["revision"],
                db.execute(
                    "SELECT COUNT(*) FROM journal WHERE world=?", (run.w,)
                ).fetchone()[0],
                db.execute(
                    "SELECT COUNT(*) FROM receipts WHERE world=?", (run.w,)
                ).fetchone()[0],
                w["chain"],
            )

    def refuse_illegal_opening(self, run):
        before = self.marks(run)
        try:
            run.store.execute(
                run.w, "illegal-open", run.v["revision"], "passage", {"step": "open"}
            )
        except engine.GameError as exc:
            assert exc.code == "unavailable", "INV-09/11"
        else:
            raise AssertionError("INV-09/11 没有获得批准的便道竟能开放")
        assert self.marks(run) == before and run.store.view(run.w) == run.v, "INV-09"
        self.counts["INV-09"] += 1
