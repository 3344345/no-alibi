"""Recognise bounded, offline player text against the actual visible action menu."""

from __future__ import annotations

import re
import unicodedata

# Aliases specify a complete intent, including qualifiers that affect the outcome.
ALIASES = {
    "掏枪": ("present_item", {"item": "restricted"}),
    "出示武器": ("present_item", {"item": "restricted"}),
    "休息": ("rest", {}),
    "在窗边休息": ("window_rest", {}),
    "全听汇报": ("report", {"mode": "full"}),
    "完整听汇报": ("report", {"mode": "full"}),
    "部分听汇报": ("report", {"mode": "short"}),
    "跳过汇报": ("report", {"mode": "skip"}),
    "暂缓签字": ("reply", {"mode": "defer"}),
    "暂缓答复": ("reply", {"mode": "defer"}),
    "有条件接收": ("reply", {"mode": "conditional"}),
    "拒绝签字": ("reply", {"mode": "decline"}),
    "委托核查": ("delegate", {}),
    "自己核查": ("compare", {}),
    "比对两份报告": ("compare", {}),
    "申请第二张照片": ("evidence", {}),
    "等待下一个事项": ("advance", {}),
}


def normalize(text):
    return re.sub(
        r"[\s·，。！？、：]+", "", unicodedata.normalize("NFKC", text)
    ).strip()


def option(action):
    return {
        k: action.get(k, default)
        for k, default in (
            ("label", ""),
            ("kind", ""),
            ("args", {}),
            ("fields", []),
            ("cost", ""),
            ("confirm", False),
        )
    }


def parse_visible(text, view):
    actions = [item for item in view.get("actions", []) if item.get("enabled", True)]
    if not view.get("ending"):
        actions.append({"kind": "advance", "label": "推进至下一事项", "args": {}})
    result, unresolved, spans = [], [], []
    ambiguous = False
    offset = 0
    for segment in re.split(r"(然后|再接着|接着|并且|以及|[；;\n])", text):
        start = offset
        offset += len(segment)
        if not segment or re.fullmatch(r"然后|再接着|接着|并且|以及|[；;\n]", segment):
            continue
        part = segment.strip()
        key = normalize(part)
        if not key:
            continue
        key = re.sub(r"^(?:(?:我想要|我想|我要|请帮我|请|先))", "", key)
        matches = [a for a in actions if normalize(a["label"]) == key]
        if not matches and key in ALIASES:
            kind, args = ALIASES[key]
            matches = [
                a for a in actions if a["kind"] == kind and a.get("args", {}) == args
            ]
        if not matches and len(key) >= 2:
            # A short fragment offers choices for clarification. Negation and qualifiers
            # never silently fall away via fuzzy substring matching in the reverse direction.
            matches = [a for a in actions if key in normalize(a["label"])]
            if matches:
                ambiguous = True
        if len(matches) != 1:
            ambiguous = True
        if not matches:
            unresolved.append(part)
        else:
            spans.append({"start": start, "end": offset, "text": part})
        for match in matches:
            public = option(match)
            if public not in result:
                result.append(public)
    if not result:
        return {
            "status": "unsupported",
            "options": [],
            "unresolved_refs": unresolved,
            "input_span_refs": [],
            "message": "当前场景没有与这句话匹配的行动。可以输入行动名称，或到「行动」里选择。",
        }
    if unresolved or ambiguous:
        note = (
            "仍需说明的部分：" + "、".join(unresolved)
            if unresolved
            else "请选择你指的具体行动。"
        )
        status = "needs_clarification"
    else:
        note = "请核对行动及代价。每一项都要单独确认。"
        status = "parsed"
    return {
        "status": status,
        "options": result,
        "unresolved_refs": unresolved,
        "input_span_refs": spans,
        "message": note,
    }
