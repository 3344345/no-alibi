from game.store import GameStore


def test_authorized_history_pages_across_revisions_and_resume(tmp_path):
    store=GameStore(tmp_path/"world.db")
    view=store.create(seed="classic")
    wid=view["world_id"]
    for i in range(203):
        view=store.execute(wid,"note-"+str(i),view["revision"],"write_note",{"text":f"史料 {i}"})
    first=store.history(wid,limit=13)
    ids=[e["id"] for e in first["events"]]
    old=first["next"]
    ref=store.execute(wid,"new",view["revision"],"write_note",{"text":"新增材料"})
    assert ref["revision"]>view["revision"]
    while old:
        batch=store.history(wid,old,13)
        ids=[e["id"] for e in batch["events"]]+ids
        old=batch["next"]
    assert len(ids)>200
    assert len(set(ids))==len(ids)
    assert ids[-200:]==[e["id"] for e in view["timeline"]]
    snapshot=store.export(wid)
    expected=[e["id"] for r in snapshot["history"][:-1] for e in r["events"] if e["visible"]]
    assert ids==expected
    assert all(set(x)=={"id","kind","minute","title","text","actor","refs"} for x in first["events"])
