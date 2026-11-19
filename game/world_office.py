"""Bounded delegation, correspondence and source-aware regional contacts."""

from .catalog import DAY, LOCATIONS, PEOPLE, STARTS
from .world_common import action, arc, case, contact, know, start_job, visible_doc


def relation(d, npc):
    links = d["actors"][npc]["relations"]
    if "player" not in links:
        familiar = npc in STARTS[d["start"]]["contacts"]
        links["player"] = {
            "trust": 0.55 if familiar else 0.4,
            "familiarity": 0.35 if familiar else 0.15,
            "dependency": 0.1,
            "competition": 0.2,
            "shared_exposure": 0,
        }
    return links["player"]


def adjust(d, npc, ref, **changes):
    # Reactions belong to a particular recipient and a particular seen event.
    if ref not in d["actors"][npc]["beliefs"]:
        return
    rel = relation(d, npc)
    applied = d["actors"][npc].setdefault("experiences", [])
    if ref in applied:
        return
    for key, amount in changes.items():
        rel[key] = round(max(0, min(1, rel[key] + amount)), 5)
    applied.append(ref)


def options(d):
    a = []
    loc = d["location"]
    flags = d["flags"]
    g = d.get("delegations", {})
    if loc == "L01" and not d["career"].get("suspended"):
        active = g.get("coord", {})
        if not active or active["state"] in ("已到期", "已撤销"):
            a.append(
                action(
                    "authority",
                    "申请限期协调签署权",
                    "向本单位负责人申请仅限本次 P01 协调意见、三天有效的书面授权。",
                    "需有权人审理",
                    "岗位授权",
                    {"mode": "request"},
                )
            )
        if active.get("state") == "生效":
            a.append(
                action(
                    "authority",
                    "交回限期授权",
                    "结束当前文件范围内的代理权限。",
                    "即时办理",
                    "岗位授权",
                    {"mode": "release"},
                )
            )
        permitted = (
            d["start"] == "S04"
            or d["career"]["rank"] >= 2
            or active.get("state") == "生效"
        )
        if permitted and not flags.get("signed_coord"):
            a.append(
                action(
                    "authority",
                    "签署南渠协调意见",
                    "仅确认职责内的协调安排，不代表财政或技术验收。",
                    "本人 15 分钟",
                    "岗位授权",
                    {"mode": "sign"},
                )
            )
        if not flags.get("wire_" + d["start"]):
            prof = STARTS[d["start"]]
            a.append(
                action(
                    "start_channel",
                    prof["channel"] + " · 报送岗位材料",
                    prof["role"]
                    + "可以使用的正式渠道，向"
                    + PEOPLE[prof["creditor"]]["name"]
                    + "报送本职材料。",
                    "按岗位核对并流转",
                    "本职事务",
                )
            )
        for npc in d["contacts"]:
            if flags.get("message/" + npc) or npc in d["busy"]:
                continue
            a.append(
                action(
                    "inquire",
                    "联系" + PEOPLE[npc]["name"],
                    "按现有渠道询问其职责内的信息；只转来已经知悉的材料。",
                    "消息服务时段",
                    "联系人物",
                    {"npc": npc},
                )
            )
        # Domestic public directory supports approaching unknown local roles through an actual introduced channel.
        unknown = [
            key
            for key in PEOPLE
            if key not in d["contacts"]
            and key < "N21"
            and not flags.get("intro/" + key)
        ]
        if unknown:
            a.append(
                action(
                    "directory",
                    "按职责申请引见",
                    "在县域名录中选择具体职能，由办公室转出书面联络请求。",
                    "工作时段排队",
                    "联系人物",
                    fields=[
                        {
                            "name": "npc",
                            "label": "申请联系的负责人",
                            "type": "select",
                            "options": [
                                {
                                    "value": i,
                                    "label": PEOPLE[i]["name"]
                                    + " · "
                                    + PEOPLE[i]["role"],
                                }
                                for i in unknown
                            ],
                            "default": unknown[0],
                            "required": True,
                        }
                    ],
                )
            )
    role = d.get("technical_rotation", {})
    if role.get("state") == "征询交接" and loc in ("L01", "L02"):
        for mode, label in [
            ("handover", "提交检查材料交接建议"),
            ("retain", "请技术员保留当前检查窗口"),
            ("neutral", "说明不干预培训选择"),
        ]:
            a.append(
                action(
                    "technician",
                    label,
                    "岗位决定由技术员和水务单位作出。已经签署的原始记录会留档。",
                    "书面回复",
                    "人物进展",
                    {"mode": mode},
                )
            )
    if d.get("mentor_change", {}).get("state") == "待回复" and loc in (
        "L01",
        "L04",
        "L05",
    ):
        for mode, label in [
            ("accept", "向新渠道递交限定材料"),
            ("decline", "保留原有联系，暂不引荐"),
        ]:
            a.append(
                action(
                    "mentor_channel",
                    label,
                    "旧联系变化已经发生，双方仍需就材料范围达成同意。",
                    "书面答复",
                    "人物进展",
                    {"mode": mode},
                )
            )
    for item in d.get("favours", {}).values():
        if item["state"] == "提出回请" and loc in ("L01", "L03"):
            for mode, title in [
                ("help", "提供约定范围的协助"),
                ("dispute", "说明先前帮助的范围"),
                ("decline", "谢绝此次回请"),
            ]:
                a.append(
                    action(
                        "favour",
                        title,
                        PEOPLE[item["from"]]["name"]
                        + "对先前帮助有自己的理解。只能办理现有职责范围内的工作。",
                        "本人 25 分钟",
                        "人情往来",
                        {"id": item["id"], "mode": mode},
                    )
                )
    # On-site dialogue addresses a specific physically present person. Long-distance calls have separate receipt events.
    for npc in LOCATIONS[loc]["people"]:
        from .world import present

        if npc not in d["contacts"] or not present(d, npc, loc):
            continue
        for mode, label in [("normal", "问近况"), ("source", "询问根据")]:
            if not flags.get("talk/" + npc + "/" + mode):
                a.append(
                    action(
                        "consult",
                        PEOPLE[npc]["name"] + " · " + label,
                        "在场直接交谈，以本人愿意公开的陈述为限。",
                        "本人 10 分钟",
                        "当面谈话",
                        {"npc": npc, "mode": mode},
                    )
                )
    return a


def act(d, k, p, ctx):
    flags = d["flags"]
    g = d.setdefault("delegations", {})
    if k == "favour":
        start_job(d, ctx, "favour_done", "办理人情回请", 25, p)
        return True
    if k == "technician":
        r = d["technical_rotation"]
        mode = p["mode"]
        r["preference"] = mode
        ref = ctx.emit(
            {
                "handover": "已将检查点清单送交水务，建议先交接再轮训。",
                "retain": "已向水务说明近期仍需技术核验。",
                "neutral": "已回复由技术员和单位商议。",
            }[mode],
            title="技术岗位回复",
        )
        arc(d, "V4-ARC01", "已提出交接意见", ref)
        return True
    if k == "mentor_channel":
        rec = d["mentor_change"]
        rec["state"] = "已回复"
        text = (
            "正式向新联络人提交限定范围的材料。"
            if p["mode"] == "accept"
            else "维持普通联系，未请求新引荐。"
        )
        ref = ctx.emit(text, title="引荐答复")
        if p["mode"] == "accept":
            ctx.schedule(
                "mentor_new_channel",
                {"ref": ref},
                ctx.duration("message_queue", 30, 75),
                title="新接件人回复",
            )
        arc(d, "V4-ARC04", text, ref)
        return True
    if k == "authority":
        mode = p["mode"]
        if mode == "request":
            source = ctx.emit(
                "限期授权申请送至政务办公室，待负责人核准。", title="授权申请"
            )
            g["coord"] = {
                "state": "待核准",
                "issuer": "N10",
                "grantee": "player",
                "scope": "P01/coordination",
                "ref": source,
            }
            ctx.schedule(
                "auth_grant",
                {"ref": source},
                ctx.duration("admin", 30, 60, working=True),
                title="办公室授权审理",
            )
        elif mode == "release":
            g["coord"]["state"] = "已撤销"
            ctx.emit("限定范围的授权已交回。", title="授权撤销")
        else:
            start_job(d, ctx, "coord_sign", "签署协调意见", 15)
        return True
    if k == "start_channel":
        start_job(
            d,
            ctx,
            k,
            STARTS[d["start"]]["channel"] + "办理",
            ctx.duration("admin", 20, 40),
        )
        return True
    if k == "directory":
        who = p["npc"]
        if who not in PEOPLE or who >= "N21" or who in d["contacts"]:
            raise ValueError("该角色不在可申请联系的县域名录中。")
        flags["intro/" + who] = True
        ref = ctx.emit("正在由办公室转出职责内联系请求。", title="引见申请")
        ctx.schedule(
            "intro_deliver",
            {"npc": who, "ref": ref},
            ctx.duration("message_queue", 30, 140, working=True),
            title="办公室联系回执",
        )
        return True
    if k == "inquire":
        who = p["npc"]
        flags["message/" + who] = True
        ref = ctx.emit(
            "已向" + PEOPLE[who]["name"] + "发出书面询问。", title="联系人物"
        )
        ctx.schedule(
            "actor_response",
            {"npc": who, "mode": "written", "ref": ref},
            ctx.duration("message_queue", 30, 90),
            title=PEOPLE[who]["name"] + "的回复",
        )
        return True
    if k == "consult":
        start_job(
            d, ctx, "actor_response", "与" + PEOPLE[p["npc"]]["name"] + "交谈", 10, p
        )
        return True
    return False


def complete(d, k, p, ctx):
    flags = d["flags"]
    g = d.setdefault("delegations", {})
    if k == "favour_request":
        who = p["who"]
        key = p["ref"]
        if key not in d["actors"][who]["beliefs"]:
            return True
        favours = d.setdefault("favours", {})
        if key in favours:
            return True
        ref = ctx.emit(
            PEOPLE[who]["name"] + "来问：上次帮忙之后，能否由你补一份资料目录？",
            title="收到回请",
            actor=who,
            refs=(key,),
        )
        if who == "N03":
            arc(d, "V4-ARC05", "协作方提出独立回请", ref)
        favours[key] = {
            "id": key,
            "from": who,
            "state": "提出回请",
            "ref": ref,
            "requested": "资料目录",
        }
        return True
    if k == "favour_done":
        item = d["favours"][p["id"]]
        mode = p["mode"]
        item["state"] = {
            "help": "已提交目录",
            "dispute": "双方保留不同理解",
            "decline": "明确谢绝",
        }[mode]
        ref = ctx.emit(
            item["state"] + "，本次回复已送达对方。",
            title="回请答复",
            refs=(item["ref"],),
        )
        know(d, item["from"], ref, item["state"])
        adjust(d, item["from"], ref, trust=0.035 if mode == "help" else -0.015)
        return True
    if k == "technician_application":
        ref = ctx.emit(
            "程向晚申请参加业务轮训。她请水务先安排已开始的检查如何交接。",
            title="来自技术员的来函",
            actor="N18",
        )
        d["technical_rotation"] = {"state": "征询交接", "ref": ref, "preference": None}
        arc(d, "V4-ARC01", "本人提出轮训申请", ref)
        ctx.schedule("technician_decision", {"ref": ref}, 3 * DAY, title="水务岗位安排")
        return True
    if k == "technician_decision":
        r = d["technical_rotation"]
        if "N18" in d["busy"]:
            due = d["busy"]["N18"]["due"] - ctx.minute + 1
            ctx.schedule(
                "technician_decision", p, max(1, due), title="在办检查交接后决定轮训"
            )
            return True
        if r["preference"] == "retain" and not d["passage"]["opened"]:
            r["state"] = "留任完成检查"
            ref = ctx.emit(
                "水务与程向晚确认延后轮训，先完成现有检查。",
                title="技术岗位决定",
                actor="N18",
            )
        else:
            r["state"] = "交接后轮训"
            ref = ctx.emit(
                "水务签收了原始检查记录。程向晚赴轮训，一周后返岗。",
                title="技术岗位决定",
                actor="N18",
            )
            start_job(d, ctx, "technician_return", "技术人员轮训", 7 * DAY, actor="N18")
        arc(d, "V4-ARC01", r["state"], ref)
        return True
    if k == "technician_return":
        d["technical_rotation"]["state"] = "轮训返岗"
        ref = ctx.emit(
            "程向晚完成轮训，恢复现场检查日程。", title="技术岗位回执", actor="N18"
        )
        arc(d, "V4-ARC01", "轮训返岗", ref)
        return True
    if k == "mentor_channel_change":
        ref = ctx.emit(
            "旧联系人完成职责更换；办公室更新了来件签收名单。",
            title="联络人调整",
            actor="N10",
            visible=False,
        )
        know(d, "N10", ref, "来件由新联系人签收。")
        d["mentor_change"] = {
            "state": "尚未通知",
            "ref": ref,
            "former": "N12",
            "new_contact": "N10",
            "authority": "N02",
        }
        d["actors"]["N12"]["resources"]["channel"] = (
            "顾问意见与介绍，原正式接件权已移交"
        )
        know(d, "N12", ref, "已交回原联络岗位，仍可提供个人建议。")
        ctx.schedule(
            "mentor_notice",
            {"ref": ref},
            ctx.duration("message_queue", 30, 100),
            title="来件渠道变更通知",
        )
        return True
    if k == "mentor_notice":
        ref = ctx.emit(
            "办公室通知：原联系人已更换。苏明川询问是否需要引荐新收件人。",
            title="渠道更新",
            actor="N10",
            refs=(p["ref"],),
        )
        d["mentor_change"]["state"] = "待回复"
        d["roles"]["N12"] = "调任后的顾问"
        ctx.schedule(
            "mentor_ally_notice",
            {"origin": ref},
            ctx.duration("message_queue", 30, 75),
            title="旧合作方收到交接消息",
            visible=False,
        )
        know(d, "N12", ref, "办公室已经送来新的接件名单。", topic="channel_update")
        case(d, "K07", "active", ref, "原人情与当前岗位职责已经分开。")
        visible_doc(
            d,
            "D07-contact",
            "办公室接件渠道更新",
            "原联系人已交接，正式材料按新接件名单递送。",
            "N10",
            "当前接件职责",
            ref=ref,
        )
        arc(d, "V4-ARC04", "收到渠道更换通知", ref)
        return True
    if k == "mentor_ally_notice":
        ref = ctx.emit(
            "蒋绍衡收到苏明川的交接通知，正式报送改经办公室。",
            title="合作安排调整",
            actor="N03",
            visible=False,
            refs=(p["origin"],),
        )
        know(d, "N03", ref, "正式接件已移至政务办公室。")
        d["actors"]["N03"]["relations"]["N12"]["dependency"] = 0.20
        d["actors"]["N03"]["plans"].append("正式来件转请周成钧协调")
        return True
    if k == "mentor_new_channel":
        ref = ctx.emit(
            "新接件人签收了限定材料，同意按书面职责协助后续联络。",
            title="新渠道建立",
            actor="N10",
            refs=(p["ref"],),
        )
        know(d, "N10", ref, "已承担本次限定联络。")
        adjust(d, "N10", ref, dependency=0.05, familiarity=0.03)
        visible_doc(
            d,
            "D07-new-contact",
            "新渠道接件回执",
            "旧引荐已转为新的限定工作联系。",
            "N10",
            "本次材料",
            ref=ref,
        )
        return True
    if k == "auth_grant":
        item = g["coord"]
        if item["state"] != "待核准" or item["ref"] != p["ref"]:
            return True
        item.update(state="生效", expiry=ctx.minute + 3 * DAY)
        ref = ctx.emit(
            "周成钧批准了本单位 P01 协调意见的三日代理签署，禁止转委托。",
            title="限期授权已送达",
            actor="N10",
            refs=(p["ref"],),
        )
        item["grant"] = ref
        ctx.schedule("auth_expire", {"ref": ref}, 3 * DAY, title="限期授权到期")
        return True
    if k == "auth_expire":
        item = g.get("coord", {})
        if item.get("grant") == p["ref"] and item["state"] == "生效":
            item["state"] = "已到期"
            ctx.emit("三日代理签署到期，岗位原有权限继续适用。", title="授权已到期")
        return True
    if k == "coord_sign":
        legal = (
            d["start"] == "S04"
            or d["career"]["rank"] >= 2
            or g.get("coord", {}).get("state") == "生效"
        )
        if not legal or d["career"].get("suspended"):
            ctx.emit("办理期间授权已经失效，协调意见未签发。", title="签发中止")
            return True
        ref = ctx.emit(
            "在有效权限内签署了南渠协调意见，未批准工程或资金。", title="协调签发"
        )
        visible_doc(
            d,
            "COORD-r1",
            "南渠协调意见",
            "本件只登记跟进分工并保留技术检查要求。",
            "本人",
            "P01 协调分工",
            ref=ref,
        )
        flags["signed_coord"] = True
        return True
    if k == "start_channel":
        prof = STARTS[d["start"]]
        who = prof["creditor"]
        wording = {
            "S01": "来文目录已注明版本和签收时间。",
            "S02": "乡镇联络授权为五万元；已报送西段巡视范围及居民来件。",
            "S03": "附上现场摘要，技术意见注明未检查区域。",
            "S04": "首轮协调方案列明三个项目均需要的班组。",
            "S05": "独立情况稿分别标明交接材料与当事人陈述。",
            "S06": "查到办理窗口并说明亲属需自行提交的程序。",
            "S07": "向市级派出方报送县里已取得的材料清单。",
            "S08": "履职材料列明自己完成的事项和待核实的成果。",
        }[d["start"]]
        ref = ctx.emit(wording, title=prof["channel"] + " · 收件回执", actor=who)
        visible_doc(
            d,
            "POST-" + d["start"],
            prof["channel"] + "收件联",
            wording,
            who,
            prof["role"],
            ref=ref,
        )
        flags["wire_" + d["start"]] = True
        know(d, who, ref, wording)
        adjust(d, who, ref, trust=0.04, familiarity=0.02)
        known = d["promises"].get("PR1")
        if known and known["status"] != "已履约":
            known["status"] = "已履约"
            case(d, "K02", "resolved", ref, wording)
        d["career"]["deliveries"] += 1
        return True
    if k == "intro_deliver":
        who = p["npc"]
        contact(d, who)
        ref = ctx.emit(
            PEOPLE[who]["name"] + "已接到办公室引见，回函附上可用联络渠道。",
            title="引见送达",
            actor=who,
            refs=(p["ref"],),
        )
        know(d, who, ref, "收到本次职责内引见函。")
        return True
    if k == "actor_response":
        who = p["npc"]
        mode = p["mode"]
        actor = d["actors"][who]
        held = actor["beliefs"]["genesis/" + who]
        from .world_templates import reply

        busy = d["busy"].get(who)
        text = reply(
            held,
            "blocked" if busy else ("source" if mode == "source" else "normal"),
            busy["title"] if busy else None,
        )
        ref = ctx.emit(
            PEOPLE[who]["name"] + "：“" + text + "”", title="人物回复", actor=who
        )
        visible_doc(
            d,
            "REPLY-" + who + "-" + mode,
            PEOPLE[who]["name"] + "的答复",
            text,
            who,
            "该人物愿意公开的信息",
            kind="人物陈述",
            ref=ref,
        )
        flags["talk/" + who + "/" + mode] = True
        know(d, who, ref, "已答复本次职责内询问。")
        adjust(d, who, ref, familiarity=0.025)
        return True
    return False
