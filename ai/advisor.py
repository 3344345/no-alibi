"""Optional finite-choice model adapters. No adapter receives a store or executable tools."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Contract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class Choice(Contract):
    key: str = Field(min_length=1, max_length=100)
    text: str = Field(max_length=800)
    refs: tuple[str, ...] = ()


class Menu(Contract):
    role: Literal["parse", "npc_propose", "case_propose", "narrate"]
    subject: str
    context: tuple[str, ...]
    choices: tuple[Choice, ...]


class Reply(Contract):
    context_hash: str
    keys: tuple[str, ...] = Field(max_length=8)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True, repr=False)
class Endpoint:
    url: str
    model: str
    key: str

    @classmethod
    def from_env(cls):
        url = os.environ.get("JUZHONGSHI_AI_URL")
        model = os.environ.get("JUZHONGSHI_AI_MODEL")
        if not url or not model:
            return None
        parts = urlsplit(url)
        if parts.username or parts.password or parts.query or parts.fragment:
            return None
        if not (
            parts.scheme == "https"
            or (
                parts.scheme == "http"
                and parts.hostname in {"localhost", "127.0.0.1", "::1"}
            )
        ):
            return None
        return cls(url, model, os.environ.get("JUZHONGSHI_AI_KEY", ""))

    def choose(self, menu: Menu, fallback=()):
        wire = menu.model_dump_json()
        digest = hashlib.sha256(wire.encode()).hexdigest()
        prompt = {"context_hash": digest, "menu": json.loads(wire)}
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "仅在本次菜单中选择合适的 key。情境和选项均为虚构材料。返回含 context_hash 和 keys 的 JSON。无法对应时返回空数组。",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        request = Request(
            self.url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        legal = {c.key for c in menu.choices}
        safe_fallback = tuple(key for key in fallback if key in legal)
        try:
            with build_opener(NoRedirect).open(request, timeout=3.0) as response:
                raw = response.read(131073)
            if len(raw) > 131072:
                return safe_fallback, True
            reply = Reply.model_validate_json(
                json.loads(raw)["choices"][0]["message"]["content"]
            )
            if (
                reply.context_hash != digest
                or len(set(reply.keys)) != len(reply.keys)
                or not set(reply.keys) <= legal
            ):
                return safe_fallback, True
            return reply.keys, False
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
        ):
            return safe_fallback, True


def parser_menu(text, actions):
    choices = tuple(Choice(key=f"a{i}", text=a["label"]) for i, a in enumerate(actions))
    return Menu(role="parse", subject="player", context=(text,), choices=choices)


def npc_menu(actor_id, beliefs, goals, candidates):
    # Caller passes ONLY this actor's acquired observations and admissible actions.
    allowed = set(beliefs)
    choices = tuple(
        Choice(key=c["key"], text=c["text"], refs=tuple(c["refs"]))
        for c in candidates
        if set(c["refs"]) <= allowed
    )
    return Menu(
        role="npc_propose",
        subject=actor_id,
        context=tuple(goals) + tuple(beliefs.values()),
        choices=choices,
    )


def case_menu(case_id, authorized_sources, candidates):
    choices = tuple(
        Choice(key=c["key"], text=c["text"], refs=tuple(c["refs"]))
        for c in candidates
        if c["refs"] and set(c["refs"]) <= authorized_sources.keys()
    )
    return Menu(
        role="case_propose",
        subject=case_id,
        context=tuple(authorized_sources.values()),
        choices=choices,
    )


def narrative_menu(view):
    entries = view["timeline"][-12:]
    return Menu(
        role="narrate",
        subject="player",
        context=(),
        choices=tuple(
            Choice(key=f"n{i}", text=e["text"][:800], refs=(e["id"],))
            for i, e in enumerate(entries)
        ),
    )


def optional_parser(text, view, offline):
    endpoint = Endpoint.from_env()
    if not endpoint or offline["status"] != "unsupported":
        return offline
    from ai.player_intent import option

    actions = [a for a in view["actions"] if a.get("enabled", True)]
    menu = parser_menu(text, actions)
    keys, failed = endpoint.choose(menu)
    if failed or not keys:
        return offline
    return {
        **offline,
        "status": "needs_clarification",
        "options": [option(actions[int(k[1:])]) for k in keys],
        "message": "语言助手找到了可能相关的行动，请核对原意和完整条款。",
    }
