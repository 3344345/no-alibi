"""The player surface exposes projections and authorized commands on loopback only."""

from __future__ import annotations

import asyncio
import json
import secrets
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from api.preferences import preferences_router
from api.confirmations import Confirmations, consequence
from ai.player_intent import parse_visible
from ai.advisor import Endpoint, narrative_menu, optional_parser
from contracts.player_view import Action, PlayerView
from contracts.player_api import (
    ActionReview,
    BranchPoint,
    NewCareer,
    ParseText,
    PlayerCommand,
)
from game.catalog import STARTS
from game import outbox
from game.store import GameError, GameStore


def problem(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        {"code": code, "message": message, "detail": message}, status_code=status
    )


def make_app(
    store: GameStore,
    token: str,
    assets: Path,
    port: int,
    preferences_path: Path | None = None,
) -> FastAPI:
    confirmations = Confirmations()
    player_view = confirmations.attach
    app = FastAPI(title="局中事", docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(preferences_router(preferences_path))
    authority = f"127.0.0.1:{port}"
    origin = f"http://{authority}"

    @app.middleware("http")
    async def local_session(request: Request, call_next):
        if request.headers.get("host") != authority:
            return problem(403, "origin", "请从本机游戏窗口打开。")
        if request.url.path.startswith("/api/"):
            if not secrets.compare_digest(
                request.headers.get("authorization", "").encode(),
                f"Bearer {token}".encode(),
            ):
                return problem(401, "session", "本次连接已失效，请从游戏入口重新打开。")
            if request.headers.get("origin", origin) != origin:
                return problem(403, "origin", "请从本机游戏窗口操作。")
            if request.method == "POST":
                if (
                    request.headers.get("content-type", "").partition(";")[0]
                    != "application/json"
                ):
                    return problem(415, "content_type", "请输入 JSON 格式的游戏数据。")
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "form-action 'none'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.exception_handler(GameError)
    async def game_error(_request, error):
        code = error.code
        status = (
            404
            if code == "not_found"
            else 409
            if code
            in {
                "revision_conflict",
                "idempotency_conflict",
                "policy_conflict",
                "history_conflict",
            }
            else 422
        )
        return problem(status, code, str(error))

    @app.exception_handler(RequestValidationError)
    async def invalid_fields(_request, _error):
        return problem(422, "invalid_input", "请检查所填字段、数值范围和格式。")

    @app.get("/api/starts")
    def list_starts():
        keys = ("id", "name", "role", "age", "channel", "brief", "obligation", "days")
        return {"starts": [{k: item[k] for k in keys} for item in STARTS.values()]}

    @app.get("/api/worlds")
    def list_games():
        return {"worlds": [player_view(v) for v in store.list_worlds()]}

    @app.post(
        "/api/worlds",
        status_code=201,
        response_model=PlayerView,
        response_model_exclude_unset=True,
    )
    def create_game(body: NewCareer):
        return player_view(
            store.create(
                start=body.start,
                name=body.name.strip(),
                balance=body.balance,
                seed=None if body.seed is None else str(body.seed),
            )
        )

    @app.get(
        "/api/worlds/{world_id}",
        response_model=PlayerView,
        response_model_exclude_unset=True,
    )
    def current(world_id: str):
        return player_view(store.view(world_id))

    @app.post(
        "/api/worlds/{world_id}/review",
        response_model=Action,
        response_model_exclude_unset=True,
    )
    def review(world_id: str, body: ActionReview):
        with confirmations.lock:
            view = store.view(world_id)
            if view["revision"] != body.expected_revision:
                return problem(
                    409, "revision_conflict", "档案已经更新，请重新查看当前条款。"
                )
            for action in view["actions"]:
                if (
                    action["kind"] == body.kind
                    and action["args"] == body.args
                    and action["enabled"]
                    and consequence(body.kind, body.args)
                ):
                    return confirmations.renew(world_id, view["revision"], action)
            return problem(422, "unavailable", "当前无法核对这项操作。")

    @app.post(
        "/api/worlds/{world_id}/commands",
        response_model=PlayerView,
        response_model_exclude_unset=True,
    )
    def act(world_id: str, body: PlayerCommand):
        with confirmations.guard(body):
            if not confirmations.accepts(world_id, body) and not store.has_receipt(
                world_id, body.command_id
            ):
                return problem(
                    409, "confirmation_required", "请重新查看当前条款，并确认这项操作。"
                )
            return player_view(
                store.execute(
                    world_id,
                    body.command_id,
                    body.expected_revision,
                    body.kind,
                    body.args,
                    provider=Endpoint.from_env(),
                )
            )

    @app.get("/api/worlds/{world_id}/commands/{command_id}")
    def receipt(world_id: str, command_id: str):
        return store.receipt(world_id, command_id)

    @app.get("/api/worlds/{world_id}/history")
    def visible_history(world_id: str, before: str | None = None, limit: int = 50):
        return store.history(world_id, before, limit)

    @app.get("/api/worlds/{world_id}/recap")
    def recent_account(world_id: str):
        view = store.view(world_id)
        rows = view["timeline"][-12:]
        menu = narrative_menu(view)
        fallback = tuple(row.key for row in menu.choices[-4:])
        endpoint = Endpoint.from_env()
        keys, local = endpoint.choose(menu, fallback) if endpoint else (fallback, True)
        selected = {
            ref for c in menu.choices if c.key in (keys or fallback) for ref in c.refs
        }
        return {
            "revision": view["revision"],
            "source": "local" if local or not keys else "provider",
            "segments": [
                {k: r[k] for k in ("id", "title", "minute", "text")}
                for r in rows
                if r["id"] in selected
            ],
        }

    @app.post("/api/worlds/{world_id}/parse")
    def parse(world_id: str, body: ParseText):
        view = store.view(world_id)
        return optional_parser(body.text, view, parse_visible(body.text, view))

    @app.post(
        "/api/worlds/{world_id}/fork",
        status_code=201,
        response_model=PlayerView,
        response_model_exclude_unset=True,
    )
    def branch(world_id: str, body: BranchPoint):
        return player_view(store.fork(world_id, body.revision))

    @app.get("/api/worlds/{world_id}/export")
    def save(world_id: str):
        return JSONResponse(
            store.export(world_id),
            headers={
                "Content-Disposition": 'attachment; filename="juzhongshi-save.json"'
            },
        )

    @app.post(
        "/api/import", response_model=PlayerView, response_model_exclude_unset=True
    )
    def restore(data: dict[str, Any] = Body()):
        return player_view(store.restore(data))

    @app.get("/api/worlds/{world_id}/events")
    async def events(world_id: str, request: Request, after: int = -1):
        await run_in_threadpool(store.view, world_id)
        last_seen = request.headers.get("last-event-id")
        cursor = (
            max(after, int(last_seen)) if last_seen and last_seen.isdecimal() else after
        )

        async def stream():
            seen = cursor
            while not await request.is_disconnected():
                changes = await run_in_threadpool(outbox.updates, store, world_id, seen)
                for change in changes:
                    seen = change["revision"]
                    data = json.dumps(change, ensure_ascii=False)
                    yield f"id: {seen}\nevent: update\ndata: {data}\n\n"
                if not changes:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(0.15 if len(changes) == 64 else 2)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/")
    def index():
        return FileResponse(assets / "index.html")

    app.mount("/", StaticFiles(directory=assets), name="web")
    return app
