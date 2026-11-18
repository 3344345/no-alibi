"""Offline release measurements using the public GameStore command path.

Fixed before running: 100 unique seeds, 12 seasons, eight rotating origins,
five anchors plus deterministic intermediate points; no discarding adverse results.
S01 with a young entrant is followed for 120 seasons unless a lawful ending fires.
Conditional sampling uses 10,000 preregistered paired uniform slots and a five-sigma
binomial band plus one observation. This is a numerical check, not human playtesting.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import hashlib
import resource
import statistics
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from game import balance
from game.engine import QUARTER_MINUTES
from game.store import GameStore
from scripts.world_invariants import WorldAudit, INVARIANTS


def quantiles(values):
    s=sorted(values)
    return {"n":len(s),"p50_ms":round(statistics.median(s)*1000,2),
            "p95_ms":round(s[math.ceil(len(s)*.95)-1]*1000,2),"max_ms":round(s[-1]*1000,2)}


class Run:
    def __init__(self,store,seed,start,b,audit=False):
        self.store=store
        self.v=store.create(start=start,name="值班联络员",balance=b,seed=seed)
        self.w=self.v["world_id"]
        self.i=0
        self.audit=WorldAudit() if audit else None
        if self.audit:
            self.audit.inspect(self)
            self.audit.refuse_illegal_opening(self)

    def send(self,k,args):
        self.i+=1
        request={"command_id":f"test-{self.i}","expected_revision":self.v["revision"],"kind":k,"args":args}
        start=time.perf_counter()
        self.v=self.store.execute(self.w,request["command_id"],request["expected_revision"],k,args)
        self.last_latency=time.perf_counter()-start
        if self.audit:self.audit.inspect(self,request)
        return self.v

    def allowed(self,k,args):
        return any(a["kind"]==k and a["args"]==args for a in self.v["actions"])

    def as_state(self):
        # Inspector is read-only; every world operation is an ordinary command.
        with self.store._db() as db:
            return json.loads(self.store._world(db,self.w)["projection"])

    def events(self):
        return [e for c in self.store.export(self.w)["history"] for e in c["events"]]


def choose_balance(i):
    anchors=("0.000000","0.250000","0.500000","0.750000","1.000000")
    return anchors[i%6] if i%6<5 else f'{balance.uniform("intermediate",str(i)):.6f}'


def twelve_seasons(path,count):
    store=GameStore(path)
    outcomes=Counter()
    levels=Counter()
    starts=Counter()
    times={"action":[],"fast_forward":[],"view":[],"replay":[]}
    variants=set()
    submitted=0
    queue_sizes=[]
    num_events=0
    invariant_counts=Counter()
    for i in range(count):
        seed=f"release-seed-{i:03d}"
        start=f"S{i%8+1:02d}"
        b=choose_balance(i)
        run=Run(store,seed,start,b,audit=True)
        starts[start]+=1; levels[b]+=1
        variants.add(run.as_state()["domain"]["variant"]["id"])
        # Fixed source/request policy. An unavailable action is skipped, never
        # replaced with a seed-dependent winning alternative.
        for kind,args in [("delegate",{}),("evidence",{}),("reply",{"mode":"conditional"}),
                          ("travel",{"location":"L03"})]:
            if run.allowed(kind,args):
                run.send(kind,args);times["action"].append(run.last_latency)
        run.send("advance",{"minutes":240})
        if run.allowed("propose",{"plan":"C"}):
            run.send("propose",{"plan":"C"});submitted+=1
        for season in range(1,13):
            target=season*QUARTER_MINUTES
            for _ in range(40):
                if run.v["ending"] or run.v["minute"]>=target:break
                t=time.perf_counter()
                run.send("advance",{"minutes":target-run.v["minute"]})
                times["fast_forward"].append(run.last_latency)
                if run.v["minute"]<target and not run.v["ending"]:
                    hearing=next((a for a in run.v["actions"] if a["kind"]=="hearing"),None)
                    assert hearing, "unexpected pause"
                    run.send(hearing["kind"],hearing["args"])
            assert run.v["ending"] or run.v["minute"]==target
            f=run.v["finances"]
            assert 0<=f["annual_remaining"]<=8_000_000_000 and 0<=f["quarter_remaining"]<=2_000_000_000
            assert 0<=f["groups_available"]<=12 and f["savings"]>=0
            if run.v["ending"]:break
        outcomes[run.v["ending"]["id"] if run.v["ending"] else "12_seasons"]+=1
        invariant_counts.update(run.audit.counts)
        state=run.as_state()
        num_events+=state["sequence"];queue_sizes.append(len(state["queue"]))
        t=time.perf_counter();view=store.view(run.w);times["view"].append(time.perf_counter()-t)
        assert view==run.v
        t=time.perf_counter();assert store.replay(run.w);times["replay"].append(time.perf_counter()-t)
    assert set(invariant_counts)==set(INVARIANTS) and all(invariant_counts.values())
    assert outcomes["12_seasons"]>0
    return {"invariant_counts":dict(sorted(invariant_counts.items())),"seeds":count,"starts":starts,"balances":levels,"variants":sorted(variants),"outcomes":outcomes,
            "proposals":submitted,"events":num_events,"terminal_queue_range":[min(queue_sizes),max(queue_sizes)],
            "timing":{k:quantiles(v) for k,v in times.items()}}


def career_bound(path):
    run=Run(GameStore(path),"release-120-quarter","S01","0.637500")
    visited=[]
    for season in range(1,121):
        target=season*QUARTER_MINUTES
        if run.v["ending"]:break
        run.send("advance",{"minutes":target-run.v["minute"]})
        visited.append((run.v["quarter"],run.v["minute"]))
        assert run.v["minute"]==target or run.v["ending"]
    assert run.v["ending"] or run.v["minute"]==120*QUARTER_MINUTES
    assert run.store.replay(run.w)
    boundary_minute, boundary_quarter = run.v["minute"], run.v["quarter"]
    boundary_events=run.as_state()["sequence"]
    # 120 seasons is a test horizon; a younger entrant can continue beyond it.
    if not run.v["ending"]:
        for _ in range(12):
            run.send("advance",{"minutes":QUARTER_MINUTES})
            if run.v["ending"]:break
        assert run.v["ending"] and run.store.replay(run.w)
    return {"requested":120,"last_quarter":boundary_quarter,"minute":boundary_minute,"commands":run.i,
            "ending":run.v["ending"]["id"],"ended_minute":run.v["minute"],"events":boundary_events}


def paired(path):
    store=GameStore(path)
    rows=[]
    for b in ("0.000000","0.250000","0.499000","0.500000","0.501000","0.750000","1.000000"):
        run=Run(store,"paired-county-2026","S04",b)
        run.send("delegate",{})
        run.send("evidence",{})
        run.send("travel",{"location":"L03"})
        run.send("advance",{"minutes":240})
        run.send("propose",{"plan":"C"})
        run.send("advance",{"minutes":200})
        events=run.events()
        costs=[e["data"] for e in events if e["kind"]=="DurationBound"]
        counter=next(e["data"] for e in events if e["kind"]=="ChoiceSealed" and "counter" in e["data"]["weights"])
        weights=counter["weights"]
        hazard=Run(store,"paired-county-2026","S04",b)
        hazard.send("compare",{});hazard.send("advance",{"minutes":25});hazard.send("advance",{"minutes":60})
        h=hazard.as_state()["clocks"]["verification"]
        rows.append({"b":b,"admin":next(c["raw"] for c in costs if c["channel"]=="admin"),
                     "message":next(c["raw"] for c in costs if c["channel"]=="message_queue"),
                     "counter":weights["counter"]/sum(weights.values()),"H":h["H"],
                     "slot":counter["slot"],"U":counter["sample"],"outcome":counter["outcome"]})
    assert len({r["slot"] for r in rows})==1 and len({r["U"] for r in rows})==1
    for a,b in zip(rows,rows[1:]):
        assert a["admin"]>b["admin"] and a["message"]>b["message"] and a["counter"]<b["counter"] and a["H"]<b["H"]
    return rows


def sampling():
    nc=10_000
    rows=[]
    us=[balance.uniform(f"reactions-{i}","offer-1") for i in range(nc)]
    for b in (0,.25,.5,.75,1):
        p=balance.counteroffer(.35,b)
        yes=sum(balance.pick({"counter":.35*balance.parameters(b)["counteroffer_weight"],"same":.65},u)=="counter" for u in us)
        assert abs(yes-nc*p)<=5*math.sqrt(nc*p*(1-p))+1
        rows.append({"b":b,"expected":p,"observed":yes/nc})
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seeds",type=int,default=100)
    parser.add_argument("--json",type=Path)
    parser.add_argument("--report",type=Path,help="render the measured results as Markdown")
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as path:
        d=Path(path)
        report={"machine":platform.machine(),"platform":platform.platform(),"python":platform.python_version(),
                "package_hash":balance.PACKAGE_HASH}
        files=sorted((ROOT/"game").glob("*.py"))+[ROOT/"PARAMETER_REGISTRY.json",Path(__file__),ROOT/"scripts"/"world_invariants.py"]
        check=hashlib.sha256()
        for f in files:check.update(f.name.encode()+b"\0"+f.read_bytes())
        report.update(source_sha256=check.hexdigest(),base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                      cpu=subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"],text=True).strip() if sys.platform=="darwin" else platform.processor(),
                      memory_bytes=int(subprocess.check_output(["sysctl","-n","hw.memsize"],text=True)) if sys.platform=="darwin" else None)
        report["paired"]=paired(d/"paired.db")
        report["sampling"]=sampling()
        report["seasons"]=twelve_seasons(d/"seasons.db",args.seeds)
        report["long"]=career_bound(d/"career.db")
        report["peak_rss"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        contents=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.json:args.json.write_text(contents)
        if args.report:
            from scripts.calibration_report import write_report
            write_report(report,args.report)
        print(contents)

if __name__=="__main__":
    main()
