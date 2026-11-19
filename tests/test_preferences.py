from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.preferences import preferences_router


def client(path):
    app = FastAPI()
    app.include_router(preferences_router(path))
    return TestClient(app)


def test_settings_are_explicit_and_survive_restarts(tmp_path):
    path = tmp_path / "ui.json"
    first, second = client(path), client(path)
    assert first.get("/api/preferences").json()["font_size"] == 16
    with ThreadPoolExecutor() as pool:
        a = pool.submit(first.post, "/api/preferences", json={"font_size": 20})
        b = pool.submit(second.post, "/api/preferences", json={"reduced_motion": True})
        assert a.result().is_success and b.result().is_success
    assert client(path).get("/api/preferences").json() == {
        "font_size": 20, "reduced_motion": True, "sound_volume": 0,
        "show_hints": True, "detailed_narration": True,
    }
    for values in [{"sound_volume": -1}, {"font_size": 64}, {"seed": 10}, {"reduced_motion": "yes"}]:
        assert first.post("/api/preferences", json=values).status_code == 422


def test_damaged_preferences_preserve_file(tmp_path):
    path = tmp_path / "ui.json"
    path.write_bytes(b"broken")
    assert client(path).post("/api/preferences", json={"sound_volume": 15}).status_code == 503
    assert path.read_bytes() == b"broken"
