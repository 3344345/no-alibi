from .catalog import CASES, DAY, PEOPLE


def action(
    kind, label, description, cost="", category="案头工作", args=None, fields=None
):
    return {
        "kind": kind,
        "label": label,
        "description": description,
        "cost": cost,
        "category": category,
        "enabled": True,
        "reason": "",
        "args": args or {},
        "fields": fields or [],
    }


def text_field(name, label, default="", limit=300):
    return {
        "name": name,
        "label": label,
        "type": "text",
        "default": default,
        "maxLength": limit,
        "required": True,
    }


def visible_doc(
    d,
    doc_id,
    title,
    body,
    actor,
    scope,
    *,
    kind="文件声称",
    version="r1",
    ref="Genesis",
    date=None,
):
    if doc_id in d["docs"]:
        return
    d["docs"][doc_id] = {
        "id": doc_id,
        "title": title,
        "name": title,
        "source": PEOPLE.get(actor, {}).get("name", actor),
        "source_id": actor,
        "date": date or f"第{1 + d['now'] // DAY}天",
        "received_minute": d["now"],
        "receipt_order": len(d["docs"]),
        "scope": scope,
        "body": body,
        "version": version,
        "kind": kind,
        "refs": [ref],
    }


def case(d, key, status, ref, detail):
    row = d["cases"].setdefault(
        key,
        {**CASES[key], "title": CASES[key]["name"], "status": "signal", "history": []},
    )
    if row["history"] and row["history"][-1]["ref"] == ref:
        return
    from .world_templates import case_line

    reopening = row["status"] in ("dormant", "resolved") and status == "active"
    row.update(status=status, detail=case_line(key, status, detail, reopening))
    row["history"].append(
        {"minute": d["now"], "ref": ref, "status": status, "text": detail}
    )


def arc(d, key, status, ref):
    row = d["arcs"].setdefault(key, [])
    if not row or row[-1]["status"] != status:
        row.append({"status": status, "ref": ref, "minute": d["now"]})


def know(d, npc, ref, text, topic=None):
    actor = d["actors"][npc]
    actor["beliefs"][ref] = text
    if topic:
        actor.setdefault("belief_topics", {})[topic] = ref


def contact(d, who):
    if who not in d["contacts"]:
        d["contacts"].append(who)


def start_job(d, ctx, kind, title, minutes, payload=None, actor="player", visible=True):
    if actor in d["busy"]:
        raise ValueError("该执行人已有安排，请等任务结束。")
    token = f"{kind}-{actor}-{d['job_seq']}"
    d["job_seq"] += 1
    d["busy"][actor] = {
        "id": token,
        "kind": kind,
        "title": title,
        "due": ctx.minute + minutes,
        "visible": visible,
    }
    args = {**(payload or {}), "_actor": actor, "_token": token}
    ctx.schedule(kind, args, minutes, title=title, visible=visible)
    return ctx.emit(
        f"{title}已列入日程，预计需 {minutes} 分钟。", title=title, visible=visible
    )


def accepted(d, payload):
    """A canceled or superseded reservation cannot complete a stale job."""
    actor = payload.get("_actor")
    if actor is None:
        return True
    if d["busy"].get(actor, {}).get("id") != payload["_token"]:
        return False
    del d["busy"][actor]
    return True


def promise(d, ctx, title, creditor, delay, kind="procedure"):
    key = "PR" + str(len(d["promises"]) + 1)
    ref = ctx.emit(f"向{PEOPLE[creditor]['name']}约定：{title}。", title="承诺已送达")
    row = {
        "id": key,
        "title": title,
        "creditor": creditor,
        "due": ctx.minute + delay,
        "status": "待履约",
        "type": kind,
        "ref": ref,
        "version": 1,
    }
    d["promises"][key] = row
    ctx.schedule(
        "promise_due", {"id": key, "version": 1}, delay, title=title + " · 到期"
    )
    return row


def readable(d):
    return d["notebook"]["location"] in ("player", d["location"])


def end_career(d, ctx, key, reason, refs=()):
    from .catalog import ENDINGS

    if d["ended"]:
        return
    from .world_templates import ending_detail

    docs = sorted(d["docs"].values(), key=lambda row: row["receipt_order"])
    reason, extra = ending_detail(
        key, reason, docs, sum(p["status"] == "待履约" for p in d["promises"].values())
    )
    refs = tuple(dict.fromkeys((*refs, *extra)))
    ref = ctx.emit(reason, title=ENDINGS[key]["name"], refs=refs)
    d["ending"] = {
        **ENDINGS[key],
        "title": ENDINGS[key]["name"],
        "description": reason,
        "refs": [ref, *refs],
        "minute": ctx.minute,
    }
    d["ended"] = True
