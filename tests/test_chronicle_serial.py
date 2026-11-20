from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from api.routes import make_app
from game.chronicle import Branch, ChronicleStore, Command, _digest
from game.chronicle_serial import SERIAL_EDITION, SERIAL_STAGES
from game.engine import GameError
from game.store import GameStore


@pytest.mark.parametrize("civil, touched", [(True, True), (False, False)])
def test_five_long_stories_share_earned_consequences_and_restore(tmp_path, civil, touched):
    store = ChronicleStore(GameStore(tmp_path / "serial.db"))
    view = store.create("年代连演", "witness", edition=SERIAL_EDITION)
    assert (view["revision"], view["chapter_count"]) == (0, 5)
    openings, prior_chapter = [], None
    while not view["finished"]:
        scene = view["scene"]
        sid = scene["id"]
        if view["chapter"]["id"] != prior_chapter:
            prior_chapter = view["chapter"]["id"]
            openings.append((prior_chapter, sid))
        available = [c["id"] for c in scene["choices"]]
        desired = {
            "xian_wait": "civil" if civil else "nanking",
            "xian_civil_first": "each",
            "sky_yard": "sky_feel" if touched else "sky_move",
            "air_dorm": "train_fitters" if touched else "draw_sizes",
            "bank_serial_table": "serial_apprentice" if civil else "serial_well",
        }
        if sid == "air_begin":
            assert ("回来那趟路费" in scene["body"]) is civil
        if sid == "night_switchboard":
            assert ("平胶布" in scene["body"]) is touched
            assert ("外线" in scene["body"] and "长一点的线" in scene["body"]) is not touched
            archive = store.export(view["id"])
            assert archive["chapters"] == [f"{SERIAL_EDITION}/{k}" for k, _ in SERIAL_STAGES]
            store = ChronicleStore(GameStore(tmp_path / "imported.db"))
            assert store.restore(archive) == view
            fork = store.fork(view["id"], Branch(revision=0))
            assert fork["edition"] == SERIAL_EDITION and fork["scene"]["id"] == "xian_wait"
        if sid == "bank_ridge":
            assert ("改衣师傅" in scene["body"]) is touched
            assert ("三张公开的纸样" in scene["body"]) is not touched
        if sid == "bank_serial_table":
            assert ("serial_apprentice" in available) is civil
            assert ("两张路费" in scene["body"]) is civil
        key = desired.get(sid, available[0])
        view = store.choose(view["id"], Command(
            revision=view["revision"], command_id=f"round-{view['revision']}", choice=key
        ))
    assert openings == list(SERIAL_STAGES)
    assert view["journal"][-1]["choice"] == ("serial_apprentice" if civil else "serial_well")
    assert view["edition"] == SERIAL_EDITION
    index = store.catalogue("witness")
    career = next(row for row in index["careers"] if row["id"] == view["id"])
    assert len(index["chapters"]) == len(store.witness.chapters)
    assert not career["standalone"] and career["finished"] and career["edition"] == SERIAL_EDITION


def test_serial_and_same_five_normal_chapters_are_distinct_even_before_first_choice(tmp_path):
    store = ChronicleStore(GameStore(tmp_path / "keep.db"))
    new = store.create("年代连演", "witness", edition=SERIAL_EDITION)
    archive = store.export(new["id"])
    ordinary = deepcopy(archive)
    ordinary["chapters"] = [ch for ch, _ in SERIAL_STAGES]
    ordinary.pop("checksum")
    ordinary["checksum"] = _digest([ordinary, []])
    with pytest.raises(GameError, match="本机已有更新或不同的档案"):
        store.restore(ordinary)

    other = ChronicleStore(GameStore(tmp_path / "normal.db"))
    restored = other.restore(ordinary)
    assert restored["scene"]["id"] == "departure" and "edition" not in restored
    assert other.export(ordinary["id"]) == ordinary
    assert other.witness.chapters[other.witness.indices["witness_gao"]].scenes[-1].id != "bank_serial_table"

    for fields in [
        {"chapters": archive["chapters"][:-1]},
        {"chapters": list(reversed(archive["chapters"]))},
        {"start_chapter": "witness_bian"}, {"campaign": "family"},
    ]:
        altered = {**archive, **fields}
        altered.pop("checksum")
        altered["checksum"] = _digest([altered, []])
        with pytest.raises(GameError, match="五章次序或起点"):
            other.restore(altered)
    assert store.view(new["id"]) == new


def test_serial_api_accepts_only_witness_with_no_individual_opening(tmp_path):
    store = GameStore(tmp_path / "api.db")
    (tmp_path / "index.html").write_text("fixture")
    client = TestClient(make_app(store, "token", tmp_path, 45711),
                        base_url="http://127.0.0.1:45711", headers={"Authorization": "Bearer token"})
    body = dict(name="年代连演", edition=SERIAL_EDITION, campaign="witness")
    for fields in ({"edition": "unknown"}, {"start_chapter": "witness_gao"},
                   {"opening_choice": "third_chair"}, {"campaign": "family"}):
        assert client.post("/api/chronicle", json={**body, **fields}).status_code == 422
    resp = client.post("/api/chronicle", json=body)
    assert resp.status_code == 201 and resp.json()["scene"]["id"] == "xian_wait"
    assert len(client.get("/api/chronicle?campaign=witness").json()["careers"]) == 1
