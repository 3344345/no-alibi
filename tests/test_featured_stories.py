from uuid import uuid4

from fastapi.testclient import TestClient

from api.routes import make_app
from game.chronicle import Branch, ChronicleStore, Command
from game.store import GameStore


def test_feature_creation_records_the_opening_atomically_and_keeps_the_ending(tmp_path):
    store = ChronicleStore(GameStore(tmp_path / "plays.db"))
    chapter = "witness_entrance_exam"
    featured = store.create("借一只袖子", "witness", chapter, "tailor_exam")
    assert featured["scene"]["id"] == "air_begin"
    assert featured["revision"] == featured["chapter_count"] == 1
    assert featured["journal"][0]["choice"] == "tailor_exam"

    for choice in ["ask_wearer", "keep_playing", "owner_cloth", "wear_gusset",
                   "send_father", "send_to_school", "draw_sizes", "make_counter",
                   "visit_band", "concert", "counter_school"]:
        featured = store.choose(featured["id"], Command(
            revision=featured["revision"], choice=choice, command_id=uuid4().hex))
    assert featured["finished"]
    assert "父亲收到的相片" in " ".join(featured["marks"])
    assert featured["journal"][-1]["label"].startswith("把校门口")
    clone = ChronicleStore(GameStore(tmp_path / "import.db"))
    assert clone.restore(store.export(featured["id"])) == featured
    branch = store.fork(featured["id"], Branch(revision=4))
    assert branch["scene"]["id"] == "air_monitor"
    entry = next(c for c in store.catalogue("witness")["careers"] if c["id"] == branch["id"])
    assert entry["standalone"] and entry["opening_choice"] == "tailor_exam"

    ordinary = store.create("完整年表", "witness", chapter)
    assert ordinary["chapter_count"] > 1 and not ordinary["journal"]
    family = store.create("两回生日", "family", opening_choice="two_birthdays")
    assert family["chapter_count"] > 1 and family["scene"]["id"] == "birthday_door"


def test_invalid_feature_is_never_listed_as_a_saved_game(tmp_path):
    store = GameStore(tmp_path / "partial.db")
    (tmp_path / "index.html").write_text("fixture")
    client = TestClient(make_app(store, "token", tmp_path, 45711),
                        base_url="http://127.0.0.1:45711", headers={"Authorization": "Bearer token"})
    response = client.post("/api/chronicle", json=dict(name="无效入口", campaign="witness",
                           start_chapter="witness_entrance_exam", opening_choice="wear_neat"))
    assert response.status_code == 422
    assert not client.get("/api/chronicle?campaign=witness").json()["careers"]
