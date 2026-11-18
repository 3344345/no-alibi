"""V4 cross-policy regressions with real county commands and a noninterference fixture."""
import builtins
import copy
import json
import math
import random
import socket
import sqlite3
import time
from pathlib import Path

import pytest

from game import balance, catalog, engine, proposals, world
from game.store import GameStore
from tests.test_world_v4 import Play

ANCHORS = ("0.000000", "0.250000", "0.500000", "0.750000", "1.000000")
Q, DAY = catalog.QUARTER, catalog.DAY


def test_v4_t03_paired_random_neighbourhood_gradients():
    rng = random.Random(40303)
    for _ in range(512):
        lo = rng.uniform(0.00001, 0.99998)
        gap = rng.uniform(1e-8, 1e-5)
        hi = lo + gap
        a, z = balance.parameters(lo), balance.parameters(hi)
        for key, slope in {"admin": -.65, "message_queue": -.55, "optional_rework": -.5,
                           "verification_rate": .8, "repair_rate": 1.2,
                           "optional_case_rate": .6, "new_soft_window": .4}.items():
            assert (z[key] - a[key])/(hi-lo) == pytest.approx(slope, abs=3e-8)
        derivative = (z["counteroffer_weight"] - a["counteroffer_weight"])/(hi-lo)
        assert math.log(2.5)-1e-7 <= derivative <= 2.5*math.log(2.5)+1e-7
        assert z["objective_weights"][1] - a["objective_weights"][1] == hi-lo


def test_v4_t11_resolver_tape_is_pure_under_io_clock_and_entropy_guards(monkeypatch):
    from game import communication, world_cases, world_career, world_projects, world_social
    # Warm imports before forbidding storage, clock and external randomness.
    g = Play(seed="guard")
    g.do("delegate")
    first = copy.deepcopy(g.s)
    command = engine.Command(command_id="guarded", expected_revision=first["revision"],
                             kind="advance", args={"minutes":Q})
    fingerprint = balance.digest(first)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("pure resolution attempted I/O, system time, or external entropy")
    with monkeypatch.context() as m:
        import os, urllib.request, subprocess, uuid
        for obj, names in [(builtins,["open"]), (Path,["open","read_bytes","read_text"]),
                           (sqlite3,["connect"]), (socket,["socket","create_connection","getaddrinfo"]),
                           (urllib.request,["urlopen"]), (subprocess,["Popen"]),
                           (time,["time","monotonic","perf_counter"]), (uuid,["uuid4"]),
                           (os,["urandom"]), (random,["random","randrange","choice","getrandbits"])]:
            for name in names: m.setattr(obj,name,forbidden)
        a, events = engine.resolve(first,command)
        b, trace = engine.resolve(first,command)
    assert balance.digest(first)==fingerprint and a==b and events==trace
    assert len(events)>5


@pytest.mark.parametrize("target", ANCHORS)
def test_v4_t12_t26_authority_inventory_location_and_shared_budget(target):
    g = Play(balance=target)
    def rejected(kind, **args):
        before=balance.digest(g.s)
        with pytest.raises(ValueError): g.do(kind,**args)
        assert balance.digest(g.s)==before
    rejected("authority",mode="sign")
    rejected("passage",step="open")
    rejected("travel",location="L05")
    g.do("write_note",text="办公室原件").do("leave_note").go("L02")
    rejected("write_note",text="无法取得的笔记")
    g.go("L03")
    assert sum(x["request"] for x in catalog.PROJECTS.values())==2400*catalog.WAN
    assert sum(x["groups"] for x in catalog.PROJECTS.values())==14
    g.do("propose",plan="A").wait(180)
    rejected("offer",offer="OF-1",choice="accept")
    g.do("permit",project="P02").do("permit",project="P03").wait(2*DAY)
    # Repeat only if a short negotiated window expired legitimately.
    if g.d["offers"][0]["status"]=="过期":
        g.do("propose",plan="A").wait(180)
    row = g.d["offers"][-1]
    g.do("offer",offer=row["id"],choice="accept")
    f=g.d["fiscal"]
    assert sum(f["groups"].values())==12
    assert 0 < f["reserved"]<=2000*catalog.WAN and f["quarter_used"]<=2000*catalog.WAN
    rejected("offer",offer=row["id"],choice="accept")
    g.wait(9*DAY)
    assert 0 <= g.d["fiscal"]["paid"] <= 8000*catalog.WAN
    assert g.d["fiscal"]["reserved"] + g.d["fiscal"]["paid"] <= 2000*catalog.WAN


@pytest.mark.parametrize("target",ANCHORS)
def test_v4_t14_same_finance_responder_real_npc_and_player_proposals(target):
    g=Play(seed="same-responder",balance=target)
    g.go("L03").do("propose",plan="C").wait(180)
    # At the hospital director's own quarterly planning turn, a sourced
    # petition reaches finance, is reviewed and a reply returns to N09.
    g.wait(10*Q)
    choices=[event["data"] for event in g.log if event["kind"]=="ChoiceSealed"]
    player=next(c for c in choices if c["slot"].startswith("fiscal/conditions/"))
    npc=next(c for c in choices if c["slot"].startswith("fiscal/npc/"))
    assert player["weights"]==npc["weights"]
    assert npc["weights"]==pytest.approx({"counter":.35 * 2.5**float(target),"same":.65})
    assert player["binding"]["balance_eff"]==npc["binding"]["balance_eff"]==float(target)
    expected=650 if npc["outcome"]=="counter" else 700
    assert any(f"医院按 {expected} 万元" in text for text in g.d["actors"]["N09"]["plans"])
    assert g.d["fiscal"]["reserved"]==0 and g.d["fiscal"]["paid"]==0


@pytest.mark.parametrize("target", ANCHORS)
def test_v4_t15_disabled_eligible_processes_never_spawn_for_quota(target):
    g=Play(seed="quiet",balance=target)
    for process in ("verification","case","rework"):
        assert not world.eligible(g.d,process)
    g.wait(4*Q)
    crossings=[event["data"]["process"] for event in g.log if event["kind"]=="OpportunityCrossed"]
    assert set(crossings) <= {"repair"}
    assert not any(proc in g.d["opportunities"] for proc in ("case","verification","rework"))
    for proc in ("case","verification","rework"):
        clock=g.s["clocks"][proc]
        assert clock["episode"]==0 and clock["H"]==0 and clock["due"] is None


@pytest.mark.parametrize("target",ANCHORS)
@pytest.mark.parametrize("variant_seed", ["11", "0", "3", "1"])
def test_v4_t32_hidden_ground_truth_cannot_change_visible_actions_or_advisor_input(target, variant_seed):
    from ai.advisor import narrative_menu
    g=Play(seed=variant_seed, balance=target)
    g.do("compare").wait(25)
    alternate=copy.deepcopy(g.s)
    alt=alternate["domain"]
    # Hold public documents and every participant's knowledge fixed while
    # replacing private project truth, an undisclosed note and a medical prior.
    alt["variant"]["answer"]="独立审计隐藏负例"
    alt["projects"]["P01"]["progress"]=57
    alt["passage"]["safe"]=not alt["passage"]["safe"]
    alt["career"]["health_profile"]["irreversible"]=not alt["career"]["health_profile"]["irreversible"]
    other=engine.player_view(alternate)
    assert engine.player_view(g.s)==other
    assert "独立审计隐藏负例" not in narrative_menu(other).model_dump_json()
    class Spy:
        def __init__(self): self.menus=[]
        def suggest(self,menu,fallback):
            self.menus.append(menu.model_dump(mode="json"))
            return fallback
    def public_inputs(d):
        spy=Spy()
        for actor in catalog.PEOPLE:proposals.npc_request(d,spy,actor)
        proposals.followup(d,spy,"N03","回访")
        return spy.menus
    assert public_inputs(g.d)==public_inputs(alt)
    for process in engine.PROCESSES:
        assert world.eligible(g.d,process)==world.eligible(alt,process)
        assert world.relevant_load(g.d,process)==world.relevant_load(alt,process)
    # With a common random tape, the two hypotheses give the same arrival
    # schedule. The differing truth may be learned by later authorized inquiry.
    cmd=engine.Command(command_id="compare-futures",expected_revision=g.s["revision"],kind="advance",args={"minutes":180})
    left, events=engine.resolve(g.s,cmd);right, other_events=engine.resolve(alternate,cmd)
    assert left["clocks"]==right["clocks"]
    assert [v for v in events if v["visible"]]==[v for v in other_events if v["visible"]]


@pytest.mark.parametrize("target", ANCHORS)
def test_v4_t31_all_scenes_projects_mentors_and_ending_with_network_blocked(tmp_path,monkeypatch,target):
    from ai.advisor import Endpoint
    blocked=[]
    def no_network(*args,**_kwargs):
        blocked.append(True)
        raise OSError("network intentionally unavailable")
    for name in ("create_connection","getaddrinfo"):
        monkeypatch.setattr(socket,name,no_network)
    monkeypatch.setattr(socket.socket,"connect",no_network)
    offline=GameStore(tmp_path/"county.db")
    degraded=GameStore(tmp_path/"degraded.db")
    v=offline.create(start="S04",seed="classic",balance=target)
    wid=v["world_id"]
    assert degraded.restore(offline.export(wid))==v
    inaccessible=Endpoint("http://127.0.0.1:9","offline-probe","")
    sequence=0
    visited={v["location"]["id"]}
    def perform(kind,**args):
        nonlocal sequence,v
        sequence+=1
        req=(wid,"cmd-"+str(sequence),v["revision"],kind,args)
        netcount=len(blocked)
        v=offline.execute(*req)
        assert len(blocked)==netcount, "offline core attempted a network connection"
        assert degraded.execute(*req,provider=inaccessible)==v
    def wait(minutes):
        perform("advance",minutes=minutes)
    def go(place):
        perform("travel",location=place)
        wait(v["busy"]["due"]-v["minute"])
        assert v["location"]["id"]==place
        visited.add(place)
    perform("write_note",text="确认收到的资料日期")
    perform("invite",choice="yes")
    perform("appointment",place="L05")
    perform("appointment",place="L06")
    wait(200)
    go("L04");perform("mentor",who="N12",mode="ask");wait(25)
    go("L02");perform("observe");wait(30)
    go("L03")
    perform("permit",project="P02");perform("permit",project="P03");wait(1500)
    perform("propose",plan="A");wait(150);perform("offer",offer="OF-1",choice="accept")
    for place in ("L05","L06","L07","L08","L09","L03"):go(place)
    wait(11*DAY)
    for pid in catalog.PROJECTS:perform("stage_check",project=pid)
    wait(450)
    assert {p["id"] for p in v["projects"] if p["public_use"]}==set(catalog.PROJECTS)
    go("L01");wait(12*Q)
    assert set(catalog.LOCATIONS)==visited and v["quarter"]>=13
    perform("career_exit",reason="leave");wait(2*DAY)
    assert v["ending"]["id"]=="END02" and blocked
    assert offline.replay(wid) and degraded.replay(wid)
    assert offline.export(wid)==degraded.export(wid)
    restored=GameStore(tmp_path/"restored.db")
    assert restored.restore(offline.export(wid))==v
