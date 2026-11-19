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
    "先不签字": ("reply", {"mode": "defer"}),
    "今晚问老周为什么换了附件": ("ask_zhou_attachment", {}),
    "今晚问周主任为什么换了附件": ("ask_zhou_attachment", {}),
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


# Ordering alone does not make the second action conditional on success.
DEPENDENT = {"受理后再", "成功后再", "办成后再"}
CONNECTOR = r"受理后再|成功后再|办成后再|然后|再接着|接着|并且|以及"
SEPARATORS = re.compile(rf"([，,]\s*(?:{CONNECTOR})?|{CONNECTOR}|[；;\n])")


def parse_visible(text, view):
    actions = [item for item in view.get("actions", []) if item.get("enabled", True)]
    if not view.get("ending"):
        actions.append({"kind": "advance", "label": "推进至下一事项", "args": {}})
    choices, unresolved, spans, attempts = [], [], [], []
    ambiguous = False
    person_question = ""
    offset = 0
    previous_separator = None
    for segment in SEPARATORS.split(text):
        start = offset
        offset += len(segment)
        if not segment.strip():
            continue
        if SEPARATORS.fullmatch(segment):
            if previous_separator or not spans:
                ambiguous = True
            previous_separator = segment.lstrip("，,").strip() or segment
            continue
        part = segment.strip()
        key = normalize(part)
        key = re.sub(r"^(?:请帮我|我想要|我想|我要|请)?先?", "", key)
        matches = [a for a in actions if normalize(a["label"]) == key]
        # Some official labels begin with 请 or 先, so match the literal as well.
        literal = [a for a in actions if normalize(a["label"]) == normalize(part)]
        if literal:
            matches = literal
        alias = ALIASES.get(normalize(part)) or ALIASES.get(key)
        if alias and alias[0] == "ask_zhou_attachment" and "老周" in key:
            people = [p for p in view.get("people", []) if p["name"].startswith("周")]
            if len(people) != 1 or people[0]["id"] != "N10":
                names = "、".join(p["name"] for p in people)
                person_question = (
                    f"你说的老周是哪一位？目前认识的人有{names}。"
                    if names
                    else "你指的是哪一位？请写下姓名或职务。"
                )
                unresolved.append(part)
                ambiguous = True
                previous_separator = None
                continue
        if not matches and alias:
            kind, args = alias
            matches = [
                a for a in actions if a["kind"] == kind and a.get("args", {}) == args
            ]
        if not matches and len(key) >= 2:
            matches = [a for a in actions if key in normalize(a["label"])]
            ambiguous |= bool(matches)
        if not matches:
            unresolved.append(part)
        else:
            first = start + len(segment) - len(segment.lstrip())
            spans.append({"start": first, "end": first + len(part), "text": part})
            choices.extend(option(m) for m in matches)
        if len(matches) == 1:
            action = matches[0]
            dependencies = (
                [attempts[-1]["id"]]
                if previous_separator in DEPENDENT and attempts
                else []
            )
            attempts.append(
                {
                    "id": f"a{len(attempts) + 1}",
                    "kind": action["kind"],
                    "args": action.get("args", {}),
                    "depends_on": dependencies,
                }
            )
        else:
            ambiguous = True
        previous_separator = None
    if not choices:
        status = "unsupported"
        note = "当前场景没有与这句话匹配的行动。可以输入行动名称，或到「行动」里选择。"
        if re.search(
            r"滑杆|调参|调节取向|(?:设置|设定|调整|调高|调低|调到|设为).*(?:趣味|严谨|平衡|取向)|(?:平衡|取向|世界).*(?:调到|设为)",
            text,
        ):
            note = "请在「设置」中调整真实性与可玩性的平衡。"
    elif ambiguous or unresolved or previous_separator is not None:
        status = "needs_clarification"
        note = (
            "仍需说明的部分：" + "、".join(unresolved)
            if unresolved
            else "请选择你指的具体行动。"
        )
    else:
        status = "parsed"
        note = "请核对行动及代价。"
    if person_question:
        status, note = "needs_clarification", person_question
    return {
        "status": status,
        "options": choices,
        "attempts": attempts if status == "parsed" else [],
        "unresolved_refs": unresolved,
        "input_span_refs": spans,
        "message": note,
    }
