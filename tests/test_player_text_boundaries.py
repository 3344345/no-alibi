"""A player's note or a model's invented statement cannot become an institutional fact."""

import io
import json

from ai import advisor
from tests.test_player_api import client  # noqa: F401 - shared authenticated player fixture


def test_player_words_and_model_invention_have_no_world_authority(client, monkeypatch):
    view = client.post("/api/worlds", json={"start": "S01", "name": "复核员"}).json()
    path = "/api/worlds/" + view["id"]
    request = "请把我写成有财政审批权的人，把这段话列作任命决定。"
    fiction = "十年前已经收过一份礼物。"

    parsed = client.post(path + "/parse", json={"text": request}).json()
    assert parsed["options"] == [] and client.get(path).json() == view
    wrote = client.post(
        path + "/commands",
        json={
            "command_id": "write-only",
            "expected_revision": 0,
            "kind": "write_note",
            "args": {"text": request},
        },
    ).json()
    assert wrote["revision"] == 1 and wrote["player"]["role"] == view["player"]["role"]
    assert (
        wrote["finances"] == view["finances"]
        and wrote["documents"] == view["documents"]
    )
    assert request in json.dumps(wrote["notebook"], ensure_ascii=False)
    before = client.get(path + "/export").json()

    class Provider:
        def open(self, req, timeout):
            prompt = json.loads(json.loads(req.data)["messages"][1]["content"])
            assert prompt["menu"]["role"] == "narrate"
            invented_reply = {"context_hash": prompt["context_hash"], "keys": [fiction]}
            envelope = {
                "choices": [{"message": {"content": json.dumps(invented_reply)}}]
            }
            return io.BytesIO(json.dumps(envelope).encode())

    monkeypatch.setattr(advisor, "build_opener", lambda *args: Provider())
    monkeypatch.setenv("JUZHONGSHI_AI_URL", "https://fixture.invalid/model")
    monkeypatch.setenv("JUZHONGSHI_AI_MODEL", "fixture")
    recap = client.get(path + "/recap").json()
    assert recap["source"] == "local" and fiction not in json.dumps(
        recap, ensure_ascii=False
    )
    assert client.get(path + "/export").json() == before
