import json
import sqlite3
from copy import deepcopy

import pytest

from game import balance, catalog
from game.store import GameStore
from scripts.inspect_game import open_snapshot


def test_v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief(tmp_path):
    for target,elapsed in [("0.000000",100),("0.500000",81),("1.000000",62)]:
        store=GameStore(tmp_path/(target+".db"))
        start=store.create(seed="mail-comparison",balance=target)
        wid=start["world_id"]
        store.execute(wid,"user-mail",0,"evidence",{})
        v=store.execute(wid,"dispatch",1,"advance",{"minutes":180})
        claims_before={}
        with open_snapshot(database=tmp_path/(target+".db")) as inspection:
            queue=inspection.inspect("queue")
            task=next(t for t in queue["tasks"] if t["kind"]=="office_delivery")
            assert task["due"]==180+elapsed
            emitted=task["payload"]["source"]
            actor=inspection.inspect("actor",actor="N09")
            claims_before=actor["beliefs"]
            assert emitted not in claims_before
            assert "D06-pool" not in {m["id"] for m in inspection.inspect("view")["documents"]}
            assert any(m["id"]=="D01-detail" for m in v["documents"])
        p=v["policy"]
        changed=store.execute(wid,"change",v["revision"],"set_balance",{
            "balance":"0.370000","expected_policy_version":p["version"],"parameter_package_hash":balance.PACKAGE_HASH})
        just_before=store.execute(wid,"before",changed["revision"],"advance",{"minutes":elapsed-1})
        with open_snapshot(database=tmp_path/(target+".db")) as inspection:
            assert claims_before==inspection.inspect("actor",actor="N09")["beliefs"]
            assert "D06-pool" not in {m["id"] for m in just_before["documents"]}
        v=store.execute(wid,"arrive",just_before["revision"],"advance",{"minutes":1})
        with open_snapshot(database=tmp_path/(target+".db")) as inspection:
            chain=inspection.inspect("chain",limit=100)
            costs=[e["data"] for e in chain["tail"] if e["kind"]=="DurationBound" and
                   e["data"]["channel"]=="message_queue" and e["data"]["floor"]==30 and e["data"]["extra"]==70]
            assert len(costs)==2 and all(x["rounded"]==elapsed for x in costs)
            after=inspection.inspect("actor",actor="N09")
            received=set(after["beliefs"])-set(claims_before)
            assert len(received)==1
            receipt_id=received.pop()
            assert after["beliefs"][receipt_id]==catalog.PEOPLE["N06"]["claim"]
            delivery=next(e for e in chain["tail"] if e["id"]==receipt_id)
            assert not delivery["visible"] and delivery["refs"]==[emitted]
            assert receipt_id not in {e["id"] for e in v["timeline"]}
            assert "D06-pool" in {m["id"] for m in v["documents"]}


def test_inspector_isolated_json_and_sqlite_and_old_version(tmp_path):
    db=tmp_path/"source.sqlite3"
    store=GameStore(db)
    first=store.create(seed="inspector");wid=first["world_id"]
    store.execute(wid,"schedule",0,"delegate",{})
    save=tmp_path/"local.json"
    save.write_text(json.dumps(store.export(wid),ensure_ascii=False))
    checks=(db.read_bytes(),save.read_bytes())
    for kwargs in ({"database":db},{"archive":save}):
        with open_snapshot(**kwargs) as inspector:
            assert inspector.inspect("view",revision=0)==first
            assert inspector.inspect("chain")["valid"]
            assert inspector.inspect("queue")["total"]>0
            assert inspector.inspect("quarantine")=={"total":0,"tasks":[]}
            with pytest.raises(ValueError):
                inspector.inspect("actor",actor="unknown")
    assert checks==(db.read_bytes(),save.read_bytes())


def test_default_inspector_has_only_an_isolated_fixture():
    with open_snapshot() as inspector:
        assert len(inspector.worlds())==1
        assert inspector.inspect("view")["name"]=="示例联络员"
