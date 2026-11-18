import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

from ai.advisor import Endpoint, case_menu, narrative_menu, npc_menu, parser_menu
from ai.player_intent import parse_visible
from api.routes import make_app
from game.store import GameStore


@pytest.fixture
def client(tmp_path):
    (tmp_path / "index.html").write_text("<title>局中事</title>")
    app = make_app(GameStore(tmp_path / "world.sqlite3"), "test-local", tmp_path, 46531)
    return TestClient(
        app,
        base_url="http://127.0.0.1:46531",
        headers={"Authorization": "Bearer test-local"},
    )


def test_auth_and_origin(client):
    assert client.get("/api/worlds", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/worlds", headers={"Host": "elsewhere"}).status_code == 403
    assert (
        client.post(
            "/api/worlds", headers={"Origin": "http://outside.invalid"}, json={}
        ).status_code
        == 403
    )
    assert client.post("/api/worlds", content="{}").status_code == 415
    assert client.get("/docs").status_code == 404


def test_career_command_recovery_and_export(client):
    assert len(client.get("/api/starts").json()["starts"]) == 8
    view = client.post(
        "/api/worlds",
        json={"start": "S01", "name": "林青", "balance": "0.501000", "seed": "classic"},
    ).json()
    url = "/api/worlds/" + view["id"]
    assert view == client.get(url).json()
    before = client.post(url + "/parse", json={"text": "先暂缓签字然后委托核查"}).json()
    assert before["status"] == "parsed" and len(before["options"]) == 2
    assert client.get(url).json()["revision"] == view["revision"]
    cmd = dict(
        command_id="first",
        expected_revision=view["revision"],
        kind="reply",
        args={"mode": "defer"},
    )
    current = client.post(url + "/commands", json=cmd).json()
    assert current["revision"] == view["revision"] + 1
    assert current == client.post(url + "/commands", json=cmd).json()
    assert (
        client.post(url + "/commands", json={**cmd, "command_id": "stale"}).status_code
        == 409
    )
    data = client.get(url + "/export").json()
    assert client.post("/api/import", json=data).json() == current
    fork = client.post(url + "/fork", json={"revision": view["revision"]}).json()
    assert fork["id"] != view["id"] and client.get(url).json() == current


def test_visible_parser_does_not_reverse_intent():
    actions = [{"label": "保证结果", "kind": "promise", "args": {}}]
    assert not parse_visible("我不保证结果", {"actions": actions})["options"]
    assert not parse_visible("我想休息", {"actions": actions})["options"]


def test_bounded_advisor_transport_and_fallback():
    payloads = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            wire = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            request = json.loads(wire["messages"][1]["content"])
            payloads.append(request)
            role = request["menu"]["role"]
            key = request["menu"]["choices"][0]["key"]
            reply = {
                "context_hash": request["context_hash"],
                "keys": [key if role != "case_propose" else "invented"],
            }
            data = json.dumps(
                {"choices": [{"message": {"content": json.dumps(reply)}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        endpoint = Endpoint(f"http://127.0.0.1:{srv.server_port}", "fixture", "")
        candidates = [
            {"key": "meet", "text": "请求会面", "refs": ["received"]},
            {"key": "secret", "text": "未送达内容", "refs": ["hidden"]},
        ]
        menus = [
            parser_menu("想了解进度", [{"label": "查看现场记录"}]),
            npc_menu("N18", {"received": "检查了西段"}, ["交付材料"], candidates),
            case_menu("K01", {"received": "已有材料"}, candidates),
            narrative_menu({"timeline": [{"id": "e1", "text": "收到回复"}]}),
        ]
        for m in menus:
            keys, fallback = endpoint.choose(m)
            assert (keys, fallback) == (
                ((), True) if m.role == "case_propose" else ((m.choices[0].key,), False)
            )
        assert "未送达内容" not in json.dumps(payloads, ensure_ascii=False)
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(2)


def test_scheduler_contains_same_minute_cycles_and_keeps_task(monkeypatch):
    from game import world
    from game.engine import Context, _advance, checked, genesis, NewCareer
    from game.event_protocol import check_event

    with pytest.raises(ValueError):
        check_event("InventedReceipt", True, None)
    settings = checked(
        NewCareer, dict(start="S01", name="查验", balance="0.500000", seed="cycle")
    )
    state, _ = genesis("cycle-test", settings)
    ctx = Context(state)
    base_complete = world.complete

    def with_loop(d, kind, args, c):
        if kind in ("test-A", "test-B"):
            c.schedule("test-B" if kind == "test-A" else "test-A", {}, 0, visible=False)
        else:
            base_complete(d, kind, args, c)

    monkeypatch.setattr(world, "complete", with_loop)
    ctx.schedule("test-A", {}, 0, visible=False)
    _advance(ctx, 1)
    saved = state["quarantine"]
    assert len(saved) == 1 and saved[0]["reason"] == "same_minute_depth"
    assert saved[0]["task"]["lineage"]["parent"]
    assert state["minute"] == 1 and not any(
        e["kind"] == "TaskQuarantined" for e in state["timeline"]
    )


def test_batch_partial_execution_and_causal_dependency(client):
    view = client.post("/api/worlds", json={"start": "S01", "name": "程雨"}).json()
    url = "/api/worlds/" + view["id"]
    attempts = [
        {"id": "a", "kind": "reply", "args": {"mode": "defer"}, "depends_on": []},
        {"id": "b", "kind": "reply", "args": {"mode": "conditional"}, "depends_on": []},
        {"id": "c", "kind": "delegate", "args": {}, "depends_on": ["b"]},
        {"id": "d", "kind": "delegate", "args": {}, "depends_on": ["a"]},
    ]
    command = {
        "kind": "batch",
        "args": {"attempts": attempts},
        "command_id": "compound",
        "expected_revision": 0,
    }
    updated = client.post(url + "/commands", json=command).json()
    assert [row["status"] for row in updated["last_action_results"]] == [
        "accepted",
        "unavailable",
        "blocked",
        "accepted",
    ]
    assert (
        updated["revision"] == 1
        and client.post(url + "/commands", json=command).json() == updated
    )
    invalid = [{**attempts[0], "depends_on": ["b"]}, attempts[1]]
    assert (
        client.post(
            url + "/commands",
            json={
                **command,
                "command_id": "invalid",
                "expected_revision": 1,
                "args": {"attempts": invalid},
            },
        ).status_code
        == 422
    )
    assert client.get(url).json() == updated


def test_confirmation_binds_terms_revision_and_receipt(client):
    view = client.post("/api/worlds", json={"start": "S01", "name": "测试"}).json()
    url = "/api/worlds/" + view["id"]
    leave = next(
        a
        for a in view["actions"]
        if a["kind"] == "career_exit" and a["args"]["reason"] == "leave"
    )
    cmd = {
        "command_id": "application",
        "expected_revision": 0,
        "kind": leave["kind"],
        "args": leave["args"],
    }
    assert client.post(url + "/commands", json=cmd).status_code == 409
    assert client.get(url + "/commands/application").json()["status"] == "unknown"
    cmd["confirmation_token"] = leave["confirmation_token"]
    assert (
        client.post(
            url + "/commands", json={**cmd, "args": {"reason": "transfer"}}
        ).status_code
        == 409
    )
    assert client.get(url).json() == view
    result = client.post(url + "/commands", json=cmd)
    assert result.status_code == 200 and result.json()["revision"] == 1
    assert client.get(url + "/commands/application").json()["status"] == "committed"
    assert client.post(url + "/commands", json=cmd).json() == result.json()


def test_explicit_high_risk_intent_absent_item_and_limited_witnesses(client):
    view = client.post("/api/worlds", json={"start": "S01", "name": "林岑"}).json()
    url = "/api/worlds/" + view["id"]
    for text, expected in (("休息", "rest"), ("在窗边休息", "window_rest")):
        draft = client.post(url + "/parse", json={"text": text}).json()
        assert {row["kind"] for row in draft["options"]} == {expected}
    draft = client.post(url + "/parse", json={"text": "掏枪"}).json()
    assert draft["status"] == "parsed" and draft["options"][0]["kind"] == "present_item"
    assert client.get(url).json() == view
    action = next(a for a in view["actions"] if a["kind"] == "present_item")
    cmd = {
        "command_id": "attempt",
        "expected_revision": view["revision"],
        "kind": action["kind"],
        "args": action["args"],
    }
    assert client.post(url + "/commands", json=cmd).status_code == 409
    after = client.post(
        url + "/commands",
        json={**cmd, "confirmation_token": action["confirmation_token"]},
    ).json()
    assert not after["ending"] and after["timeline"][-1]["kind"] == "AttemptUnfulfilled"
    history = client.get(url + "/export").json()["history"][-1]["events"]
    witnesses = [e for e in history if e["title"] == "在场观察"]
    assert witnesses and {e["actor"] for e in witnesses} <= {
        p["id"] for p in view["people"] if p["present"]
    }
    assert all(
        not e["visible"] and e["refs"] == [after["timeline"][-1]["id"]]
        for e in witnesses
    )


@pytest.mark.parametrize(
    "failure",
    [
        "offline",
        "timeout",
        "429",
        "malformed",
        "refusal",
        "stale",
        "unknown",
        "excessive",
    ],
)
def test_optional_provider_falls_back_without_mutating_world(monkeypatch, failure):
    import io
    from urllib.error import HTTPError, URLError
    import ai.advisor as advisor

    menu = parser_menu("不确定", [{"label": "请求会面"}])

    class Opener:
        def open(self, request, timeout):
            assert timeout <= 3
            if failure == "offline":
                raise URLError("unavailable")
            if failure == "timeout":
                raise TimeoutError()
            if failure == "429":
                raise HTTPError("https://provider.invalid", 429, "", {}, None)
            if failure == "malformed":
                return io.BytesIO(b"!invalid")
            if failure == "excessive":
                return io.BytesIO(b"X" * 131073)
            if failure == "refusal":
                return io.BytesIO(b'{"choices":[{"message":{"refusal":"declined"}}]}')
            h = hashlib.sha256(menu.model_dump_json().encode()).hexdigest()
            reply = {
                "context_hash": "old" if failure == "stale" else h,
                "keys": ["invented" if failure == "unknown" else "a0"],
            }
            return io.BytesIO(
                json.dumps(
                    {"choices": [{"message": {"content": json.dumps(reply)}}]}
                ).encode()
            )

    monkeypatch.setattr(advisor, "build_opener", lambda *a: Opener())
    assert Endpoint("https://provider.invalid", "local-fixture", "").choose(
        menu, ("a0",)
    ) == (("a0",), True)


def test_model_candidates_can_change_only_registered_speech_and_never_recall_on_retry(
    tmp_path,
):
    q = 90 * 1440
    s = GameStore(tmp_path / "world.sqlite3")
    v = s.create(seed="candidate-integration")

    # Once the recipient has received one actual message, their next contact may
    # choose an inquiry about that material instead of repeating their initial claim.
    class Provider:
        model = "transport-fixture"

        def __init__(self):
            self.seen = []

        def choose(self, menu):
            self.seen.append(menu)
            return (menu.choices[-1].key,), False

    fake = Provider()
    wid = v["world_id"]
    for i in range(40):
        cmd = dict(
            world_id=wid,
            command_id=f"quarter-{i}",
            expected_revision=v["revision"],
            kind="advance",
            args={"minutes": q},
        )
        v = s.execute(**cmd, provider=fake)
        if fake.seen:
            old = len(fake.seen)
            assert s.execute(**cmd, provider=fake) == v and len(fake.seen) == old
            break
    assert fake.seen and all(
        m.role in ("npc_propose", "case_propose") for m in fake.seen
    )
    events = [event for r in s.export(wid)["history"] for event in r["events"]]
    assert any(
        e["kind"] == "ModelCandidateApplied" and not e["visible"] for e in events
    )
    assert s.replay(wid) and len(fake.seen) == old
