"""Playable county pathways through command resolution, without injecting fixture events."""

import json
import pytest
from game import catalog, engine, world
from contracts.player_view import PlayerView
from game.store import GameStore

Q = catalog.QUARTER
D = catalog.DAY


class Play:
    def __init__(self, start="S01", seed="classic", balance="0.500000"):
        options = engine.NewCareer(start=start, name="林青", balance=balance, seed=seed)
        self.s, _ = engine.genesis("route", options)
        self.log = []

    @property
    def d(self):
        return self.s["domain"]

    def do(self, kind, **args):
        cmd = engine.Command(
            command_id=f"r{self.s['revision']}",
            expected_revision=self.s["revision"],
            kind=kind,
            args=args,
        )
        self.s, events = engine.resolve(self.s, cmd)
        visible = engine.player_view(self.s)
        PlayerView.model_validate({**visible, "id": visible["world_id"]})
        self.log += events
        return self

    def wait(self, n):
        return self.do("advance", minutes=n)

    def go(self, dest):
        self.do("travel", location=dest)
        self.wait(self.d["busy"]["player"]["due"] - self.s["minute"])
        assert self.d["location"] == dest
        return self


@pytest.mark.parametrize("sid", list(catalog.STARTS))
def test_start_only_sees_own_prior_and_can_do_own_job(sid):
    g = Play(start=sid)
    v = world.project(g.d)
    assert v["player"]["role"] == catalog.STARTS[sid]["role"]
    assert len(v["locations"]) == 9
    assert "variant" not in v and "actors" not in v
    assert all("progress" not in p for p in v["projects"])
    g.do("start_channel").wait(100)
    assert g.d["promises"]["PR1"]["status"] == "已履约"
    assert "POST-" + sid in g.d["docs"]


def test_service_and_accessible_evidence_with_divergent_paths():
    g = Play()
    g.do("delegate").go("L02").do("observe").wait(30)
    assert "D01-index" in g.d["docs"] and "OBS-site" in g.d["docs"]
    g.do("evidence").wait(200)
    assert "20" in g.d["docs"]["D01-detail"]["body"]
    with pytest.raises(ValueError):
        g.do("passage", step="open")
    for step in ("inspect", "approve", "open"):
        g.do("passage", step=step).wait(150)
    assert g.d["passage"]["opened"] and g.d["projects"]["P01"]["progress"] == 20
    g.go("L01")
    assert world.travel_time(g.d, "L02") == 40
    g.do("revise").wait(30)
    assert g.d["docs"]["D01-r2"]["version"] == "r2"
    assert g.d["docs"]["D01-r1"]["body"] != g.d["docs"]["D01-r2"]["body"]


def test_all_four_frozen_explanations_and_repair():
    variants = {}
    for i in range(100):
        g = Play(seed=str(i))
        v = g.d["variant"]
        variants.setdefault(v["id"], (g, v["answer"]))
        if len(variants) == 4:
            break
    assert len({x[1] for x in variants.values()}) == 4
    for g, answer in variants.values():
        original = g.d["variant"].copy()
        g.do(
            "set_balance",
            balance="0.863527",
            expected_policy_version=g.s["policy"]["version"],
            parameter_package_hash=engine.bal.PACKAGE_HASH,
        )
        g.do("evidence").wait(250)
        assert (
            g.d["variant"] == original and g.d["docs"]["D01-detail"]["body"] == answer
        )
    g = variants["V4-TV04"][0]
    g.do("passage", step="inspect").wait(150)
    assert g.d["passage"]["stage"] == "待整改"
    g.do("passage", step="repair").wait(150)
    assert g.d["fiscal"]["paid"] == 20 * catalog.WAN
    g.do("passage", step="inspect").wait(150)
    assert g.d["passage"]["stage"] == "检查通过"


def test_conditional_budget_and_real_work():
    g = Play()
    g.go("L03").do("propose", plan="A").wait(175)
    with pytest.raises(ValueError):
        g.do("offer", offer="OF-1", choice="accept")
    for key in ("P02", "P03"):
        g.do("permit", project=key)
    g.wait(250).do("offer", offer="OF-1", choice="accept")
    f = g.d["fiscal"]
    reserved = f["reserved"]
    assert 0 < reserved <= 2000 * catalog.WAN and sum(f["groups"].values()) == 12
    g.do("cancel_reservation", project="P02").wait(9 * D)
    assert (
        sum(g.d["fiscal"]["groups"].values()) == 0 and g.d["fiscal"]["paid"] < reserved
    )
    assert g.d["projects"]["P02"]["phase"] == "拟议"
    g.do("stage_check", project="P03").wait(400)
    assert g.d["projects"]["P03"]["opened"] and not g.d["projects"]["P02"]["opened"]
    g.wait(Q)
    assert g.d["projects"]["P03"]["maintenance_due"]


def test_notebook_private_and_clocked_exposure():
    g = Play()
    g.do("write_note", text="个人推测，与地点和时间尚待核实。").do("leave_note")
    g.go("L02")
    assert world.project(g.d)["notebook"]["entries"] == []
    assert "个人推测，与地点和时间尚待核实。" not in json.dumps(
        engine.player_view(g.s), ensure_ascii=False
    )
    g.wait(150)
    assert g.d["cases"]["K13"]["status"] == "contested"
    g.go("L01").do("take_note").do("copy_note").wait(30)
    g.do("destroy_note").do("confirm_note", choice="yes")
    assert g.d["notebook"]["location"] == "destroyed" and g.d["notebook"]["copies"]
    g.do("refer", document="NB-copy-1").wait(180).do("review", mode="origin").wait(200)
    assert (
        g.d["investigation"]["status"] == "已归档"
        and not g.d["investigation"]["findings"]
    )


def test_role_grant_lease_and_reject_forgery():
    g = Play()
    with pytest.raises(ValueError):
        g.do("authority", mode="sign")
    with pytest.raises(ValueError):
        g.do("inquire", npc="N24")
    with pytest.raises(ValueError):
        g.do("directory", npc="N24")
    g.do("authority", mode="request").wait(180)
    g.do("authority", mode="sign").wait(20)
    assert "COORD-r1" in g.d["docs"]
    g.wait(3 * D)
    assert g.d["delegations"]["coord"]["state"] == "已到期"


@pytest.mark.parametrize("reason,terminal", [("leave", "END02"), ("transfer", "END04")])
def test_exit_after_real_handover(reason, terminal):
    g = Play()
    g.do("career_exit", reason=reason)
    assert not g.d["ended"]
    g.wait(2 * D)
    if reason == "transfer":
        assert g.d["career"]["transferred"] and not g.d["ended"]
        g.do("stage_end", id="END04")
    assert g.d["ending"]["id"] == terminal


@pytest.mark.parametrize("decision,terminal", [("exit", "END05"), ("file", "END06")])
def test_acquired_evidence_and_formal_ending(decision, terminal):
    g = Play()
    g.do("appointment", place="L05").wait(180).go("L05").do("gift", choice="take").go(
        "L01"
    )
    assert g.d["investigation"]["status"] == "无程序"
    g.do("refer", document="GIFT-take").wait(180).do("review", mode="origin").wait(
        3 * D
    )
    assert world.decision_pending(g.d)
    with pytest.raises(ValueError):
        g.wait(10)
    g.do("hearing", mode="written").wait(300)
    assert not g.d["ended"] and g.d["career"]["suspended"]
    g.do("finding", mode=decision)
    if decision == "exit":
        g.wait(120)
    assert g.d["ending"]["id"] == terminal


def test_marginal_exit_requires_history_and_intent():
    g = Play()
    g.do("invite", choice="yes").go("L04").do("speak", mode="limited").wait(20).go(
        "L01"
    ).wait(4 * Q)
    assert g.d["career"]["duties"] != "正常" and not g.d["ended"]
    g.do("career_exit", reason="marginal").wait(D)
    assert g.d["ending"]["id"] == "END03"


def test_late_career_retirement_care_and_health_records():
    g = Play(start="S06", seed="classic")
    g.wait(110 * Q)
    assert g.d["ending"]["id"] == "END01"
    h = Play(seed="19")
    n = h.d["career"]["health_window"]
    h.wait((n - 1) * Q)
    h.do("career_exit", reason="care").wait(3 * D)
    assert h.d["ending"]["id"] == "END07"
    j = Play(seed="19")
    j.wait(120 * Q)
    assert (
        j.d["ending"]["id"] == "END08" and j.d["career"]["illness"] == "死亡记录已送达"
    )
    assert any(e["title"] == "既有病程的随访通知" for e in j.log)


def test_family_and_mentor_paths_have_independent_consequences():
    g = Play()
    g.go("L07").do("family_plan", mode="cover").wait(40).wait(7 * D)
    assert g.d["family"]["plan_end"] > g.s["minute"] and not world.present(
        g.d, "N14", "L07"
    )
    g.go("L08").do("mentor", who="N13", mode="verify").wait(D)
    assert g.d["cases"]["K12"]["status"] == "resolved"
    assert g.d["actors"]["N13"]["belief_topics"]["channel_update"]


def test_offline_store_replay_from_real_actions(tmp_path):
    st = GameStore(tmp_path / "world.db")
    v = st.create("S04", "林青", "0.376231", "classic")
    wid = v["world_id"]
    for i, (k, p) in enumerate(
        [
            ("delegate", {}),
            ("travel", {"location": "L02"}),
            ("advance", {"minutes": 160}),
            ("observe", {}),
            ("advance", {"minutes": 40}),
        ]
    ):
        v = st.execute(wid, "real-" + str(i), v["revision"], k, p)
    assert st.view(wid) == v
    # Replay API validates each stored command, its causal envelope and effect chain.
    replay = st.replay(wid)
    assert replay is True
    assert any(x["id"] == "OBS-site" for x in v["documents"])


def test_cooperation_materials_sustain_a_complete_position_chain():
    g = Play(seed="classic")
    g.do("start_channel").wait(100)
    g.do("delegate").wait(200).do("revise").wait(60)
    g.go("L03").do("cooperate").wait(200)
    assert g.d["actors"]["N03"]["beliefs"]
    obligation = next(iter(g.d["favours"].values()))
    g.do("favour", id=obligation["id"], mode="dispute").wait(30)
    assert g.d["favours"][obligation["id"]]["state"] == "双方保留不同理解"
    g.go("L01")
    reached = set()
    for _ in range(90):
        c = g.d["career"]
        reached.add(c["rank"])
        if c["rank"] == 5:
            break
        if c["rank"] >= 2 and not c.get("cross_record"):
            g.do("cross_review").wait(70)
        if c["vacancy"] and not c["applied"]:
            g.do("nominate", mode="self").wait(2 * D)
        if g.d["career"]["rank"] != c["rank"]:
            continue
        g.wait(Q - g.s["minute"] % Q)
    assert reached == set(range(6))


def test_invitation_refusal_and_actual_arrival_have_separate_witnesses():
    g = Play()
    g.do("invite", choice="later")
    assert "K05" not in g.d["cases"]
    g.go("L04")
    assert g.d["cases"]["K05"]["status"] == "contested"
    g.do("speak", mode="limited").wait(15)
    speech = g.d["statements"][-1]
    assert (
        speech["audience"] == ["N17"]
        and speech["ref"] in g.d["actors"]["N17"]["beliefs"]
    )
    assert speech["ref"] not in g.d["actors"]["N07"]["beliefs"]
    g.wait(300)
    assert "K11" in g.d["cases"]
    g.do("clarify").wait(300)
    assert g.d["cases"]["K11"]["status"] == "resolved"


def test_technician_keeps_pending_work_and_can_legally_change_schedule():
    keep = Play()
    keep.wait(2 * D)
    keep.do("technician", mode="retain").wait(4 * D)
    assert keep.d["technical_rotation"]["state"] == "留任完成检查"
    travel = Play()
    travel.wait(2 * D)
    travel.do("technician", mode="handover").wait(4 * D)
    assert not world.present(travel.d, "N18", "L02")
    assert not any(a["kind"] == "evidence" for a in world.actions(travel.d))
    travel.wait(8 * D)
    assert travel.d["technical_rotation"]["state"] == "轮训返岗"


def test_register_matches_world_and_all_32_mechanisms():
    from scripts.content_manifest import manifest, ROOT

    built = manifest()
    assert built == json.loads((ROOT / "CONTENT_MANIFEST.json").read_text())
    counts = {
        "starts": 8,
        "locations": 9,
        "actors": 24,
        "projects": 3,
        "cases": 16,
        "scenes": 10,
        "arcs": 6,
        "endings": 8,
        "mechanisms": 32,
    }
    for k, n in counts.items():
        assert len(built[k]) == n
        assert len({row["id"] for row in built[k]}) == n


def test_all_cases_can_receive_new_material_after_three_quarters():
    from game.world_cases import available

    g = Play()
    g.do("invite", choice="later").go("L04").do("speak", mode="assure").wait(200)
    assert any(x.startswith("SPEECH-reliance-") for x in g.d["docs"])
    assert g.d["fiscal"]["paid"] == 0
    g.do("clarify").wait(180).go("L08").do("mentor", who="N13", mode="verify").wait(180)
    g.go("L07").do("family_plan", mode="cover").wait(40).go("L01")
    g.do("start_channel").wait(80).do("delegate").do("evidence").wait(200).do(
        "revise"
    ).wait(35)
    g.do("permit", project="P02").do("permit", project="P03").wait(2 * D)
    g.do("write_note", text="对项目口径的一条个人判断").do("copy_note").wait(30)
    g.do("destroy_note").do("confirm_note", choice="yes")
    g.go("L03").do("cooperate").wait(100).do("propose", plan="A").wait(150).do(
        "offer", offer="OF-1", choice="accept"
    )
    g.go("L01").do("career_exit", reason="transfer").wait(2 * D)
    g.do("advance", minutes=15 * D)
    g.go("L02").do("observe").wait(35).do("passage", step="inspect").wait(200)
    g.go("L01").wait(7 * Q)
    assert set(g.d["cases"]) == set(catalog.CASES)
    # Leave all source material and outstanding issues in the save for three more quarters.
    g.wait(3 * Q)
    for key in sorted(catalog.CASES):
        row = g.d["cases"][key]
        if row["status"] not in ("resolved", "dormant"):
            g.do("case_file", case=key, mode="shelve")
        docs = available(g.d, key)
        assert docs, key
        pick = docs[0]["id"]
        g.do("case_file", case=key, mode="submit", document=pick).wait(180)
        row = g.d["cases"][key]
        assert any("依据新的材料重开" in entry["text"] for entry in row["history"]), key
        assert row["history"][-1]["minute"] - row["history"][0]["minute"] >= 3 * Q, key
        assert row["reviewed_docs"] == [pick], key
        with pytest.raises(ValueError):
            g.do("case_file", case=key, mode="submit", document=pick)


def test_six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes():
    def statuses(g, key):
        steps = g.d["arcs"][key]
        assert all(s["ref"].startswith("route/e") for s in steps)
        return {s["status"] for s in steps}

    outcomes = {key: set() for key in catalog.ARCS}
    for selected in (False, True):
        g = Play()
        g.do("delegate").do("evidence").wait(200).do("revise").wait(50).do(
            "start_channel"
        ).wait(120)
        g.do("invite", choice="yes").go("L04").do("mentor", who="N12", mode="ask").wait(
            25
        )
        g.do("mentor", who="N12", mode="verify").wait(140)
        g.go("L07").do("family_plan", mode="cover" if selected else "decline").wait(40)
        g.go("L03").do("cooperate").wait(180).do("propose", plan="C").wait(180)
        if selected:
            g.do("offer", offer="OF-1", choice="accept")
        g.go("L01").wait(2 * D).do(
            "technician", mode="handover" if selected else "retain"
        )
        g.wait(9 * D).do("mentor_channel", mode="accept" if selected else "decline")
        for _ in range(15):
            g.wait(Q - g.s["minute"] % Q)
            c = g.d["career"]
            if c["vacancy"]:
                if selected and g.d["quarter"] - c["since"] < 4:
                    continue
                g.do("nominate", mode="self" if selected else "peer").wait(2 * D)
                break
        per_arc = {key: statuses(g, key) for key in catalog.ARCS}
        for key, steps in per_arc.items():
            assert len(steps) >= 3, (key, steps)
        ends = {
            "V4-ARC01": "交接后轮训" if selected else "留任完成检查",
            "V4-ARC02": "已支付并交付计量记录" if selected else "暂缓分配",
            "V4-ARC03": "完成独立职业安排" if selected else "自行选择下一期培训",
            "V4-ARC04": "正式向新联络人提交限定范围的材料。"
            if selected
            else "维持普通联系，未请求新引荐。",
            "V4-ARC05": "本人获任" if selected else "协作者获任",
            "V4-ARC06": "本人接任" if selected else "其他候选人接任",
        }
        for key, ending in ends.items():
            assert ending in per_arc[key], (key, ending, per_arc[key])
            assert len(per_arc[key] - {ending}) >= 3, (key, ending, per_arc[key])
            outcomes[key].add(ending)
    assert all(len(x) == 2 for x in outcomes.values())


def test_sourced_notes_arrive_in_custody_then_receive_partial_corroboration():
    g = Play()
    g.go("L07")
    g.do(
        "write_sourced_note",
        text="简报写的是总项目进度。",
        document="D01-r1",
        classification="引用文件",
    )
    g.do("copy_note").wait(20)
    copy = g.d["notebook"]["copies"][0]
    assert copy["holder"] == "传递中"
    assert copy["ref"] not in g.d["actors"]["N19"]["beliefs"]
    g.do("destroy_note").do("confirm_note", choice="yes").wait(180)
    assert g.d["notebook"]["copies"][0]["holder"] == "N19"
    g.go("L01").do("refer", document=copy["id"]).wait(180).do(
        "review", mode="origin"
    ).wait(300)
    assert "D01-r1" in g.d["investigation"]["acquired"]
    assert any(k.startswith("NB-ver") for k in g.d["docs"])
    assert (
        g.d["investigation"]["status"] == "已归档"
        and not g.d["investigation"]["findings"]
    )


def test_refund_enters_case_only_when_received_from_counterparty():
    g = Play()
    g.do("appointment", place="L05").wait(180).go("L05")
    g.do("gift", choice="take").do("gift", choice="return").go("L01")
    g.do("refer", document="GIFT-take").wait(180)
    assert "GIFT-return" not in g.d["investigation"]["acquired"]
    g.do("review", mode="origin").wait(D)
    assert (
        g.d["investigation"]["return_witness"]
        and "GIFT-return" in g.d["investigation"]["acquired"]
    )
    g.do("hearing", mode="attend").wait(300)
    assert not g.d["career"].get("suspended")


def test_institution_can_appoint_a_new_identity_without_copying_private_beliefs():
    # At C1 the target is C2. Recommend the local eligible peer, then a new
    # qualified external successor when the first appointee's own term ends.
    g = Play(start="S04")
    g.wait(14 * Q)
    assert g.d["successors"]
    row = next(iter(g.d["successors"].values()))
    key = row["id"]
    assert key not in catalog.PEOPLE and row["origin"]
    assert key in g.d["actors"] and key in {
        x["id"] for x in world.project(g.d)["people"]
    }
    assert not set(g.d["actors"][key]["beliefs"]).intersection(
        g.d["actors"]["N03"]["beliefs"]
    )
    assert len(g.d["actors"][key]["beliefs"]) == 2


def test_step_auditor_catches_hidden_fields_in_public_view(tmp_path):
    from scripts.calibrate import Run
    from scripts.world_invariants import WorldAudit

    run = Run(GameStore(tmp_path / "audit.sqlite3"), "audit-hidden", "S01", "0.500000")
    run.v["player"]["rng_seed"] = "should-be-hidden"
    with pytest.raises(AssertionError, match="INV-05"):
        WorldAudit().inspect(run)


def test_step_auditor_catches_mutated_logged_random_outcome(tmp_path):
    from scripts.calibrate import Run
    from scripts.world_invariants import WorldAudit

    run = Run(GameStore(tmp_path / "audit.sqlite3"), "audit-choice", "S01", "0.500000")
    audit = WorldAudit()
    audit.inspect(run)
    for k, args in [
        ("travel", {"location": "L03"}),
        ("advance", {"minutes": 45}),
        ("propose", {"plan": "C"}),
    ]:
        run.send(k, args)
        audit.inspect(run)
    run.send("advance", {"minutes": 200})
    # Corrupt the fixture's tail record while preserving all game-state effects.
    # The stored projection therefore still matches, but its random evidence does not.
    with run.store._db(write=True) as db:
        row = db.execute(
            "SELECT value FROM journal WHERE world=? AND revision=?",
            (run.w, run.v["revision"]),
        ).fetchone()
        record = json.loads(row[0])
        draw = next(x["data"] for x in record["events"] if x["kind"] == "ChoiceSealed")
        draw["sample"] = (draw["sample"] + 0.5) % 1
        db.execute("DROP TRIGGER journal_no_update")
        db.execute(
            "UPDATE journal SET value=? WHERE world=? AND revision=?",
            (json.dumps(record), run.w, run.v["revision"]),
        )
    with pytest.raises(AssertionError, match="INV-10"):
        audit.inspect(run)
