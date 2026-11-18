"""Office circulation. A statement joins the recipient's beliefs only on delivery."""

from .catalog import PEOPLE, PROJECTS, WAN
from .negotiation import choose_reply
from .world_common import arc, case, know, visible_doc


def send_plan(domain, sender, ctx):
    person = PEOPLE[sender]
    recipient = person["contact"]
    actor = domain["actors"][sender]
    from .proposals import npc_request

    body = npc_request(domain, ctx, sender)
    dispatch = ctx.emit(
        person["name"] + "发出职责内联络，原话为「" + body + "」。",
        title=person["plan"],
        actor=sender,
        visible=False,
    )
    actor["last_acted"] = dispatch
    # Finance circulates the original three-project budget to the office once.
    # Later contacts only receive the actual statement aimed at that recipient.
    copy_office = sender == "N06" and not domain["flags"].get("budget_circular_sent")
    if copy_office:
        domain["flags"]["budget_circular_sent"] = True
    message = {
        "sender": sender,
        "recipient": recipient,
        "body": body,
        "source": dispatch,
        "copy_office": copy_office,
    }
    if (
        sender == "N09"
        and recipient == "N06"
        and domain["projects"]["P03"]["phase"] == "拟议"
    ):
        # The hospital submits its own registered stage request at its scheduled
        # planning turn. This is an application; it creates no reservation.
        message["stage_request"] = {
            "amount": PROJECTS["P03"]["request"],
            "groups": PROJECTS["P03"]["groups"],
            "quarter": domain["quarter"],
        }
    delay = ctx.duration("message_queue", 30, 70)
    ctx.schedule(
        "office_delivery",
        message,
        delay,
        title="财政协调函预计送达" if copy_office else "职责内来函",
        visible=copy_office,
    )


def deliver_plan(domain, message, ctx):
    if message.get("stage") == "review":
        return review_hospital_request(domain, message, ctx)
    sender, recipient = message["sender"], message["recipient"]
    source = message["source"]
    receipt = ctx.emit(
        PEOPLE[recipient]["name"] + "收到" + PEOPLE[sender]["name"] + "的来函。",
        title="职责内收文",
        actor=recipient,
        visible=False,
        refs=(source,),
    )
    know(domain, recipient, receipt, message["body"])
    if "stage_request" in message:
        ctx.schedule(
            "office_delivery",
            {"stage": "review", "request": message["stage_request"], "source": receipt},
            ctx.duration("admin", 30, 100),
            visible=False,
        )
    if message.get("stage") == "reply":
        plans = domain["actors"][recipient]["plans"]
        if message["body"] not in plans:
            plans.append(message["body"])
    if message["copy_office"]:
        office = ctx.emit(
            "许慎川的首季协调函和三项目资源清单已送达办公室。",
            title="财政首轮协调函",
            actor=sender,
            refs=(source,),
        )
        visible_doc(
            domain,
            "D06-pool",
            "三项目资源清单",
            "年度额度 8000 万元，首季可拨付 2000 万元。三项请求合计 2400 万元、14 组。",
            sender,
            "首季预算",
            ref=office,
        )
        case(domain, "K09", "signal", office, "财政送达了首轮汇总。")
        arc(domain, "V4-ARC02", "财政征集分期方案", office)


def review_hospital_request(domain, message, ctx):
    request = message["request"]
    amount, groups = request["amount"], request["groups"]
    fiscal = domain["fiscal"]
    available = min(fiscal["annual_left"], 2000 * WAN - fiscal["quarter_used"])
    if domain["projects"]["P03"]["phase"] != "拟议":
        return
    if available < amount or 12 - sum(fiscal["groups"].values()) < groups:
        body = "本轮未能落实容量。医院下轮再提交分区安排。"
    else:
        slot = f"fiscal/npc/P03/{request['quarter']}/{amount}/{groups}"
        # Finance evaluates the same feasible fiscal response group as it does
        # for a player submission. Neither proposal transfers a cent on its own.
        if choose_reply(ctx, slot, 0.35) == "counter":
            amount -= 50 * WAN
        body = f"医院按 {amount // WAN} 万元、{groups} 组的范围准备分区材料，拨付另行审核。"
    ref = ctx.emit(
        body,
        title="财政答复医院",
        actor="N06",
        visible=False,
        refs=(message["source"],),
    )
    ctx.schedule(
        "office_delivery",
        {
            "stage": "reply",
            "sender": "N06",
            "recipient": "N09",
            "body": body,
            "source": ref,
            "copy_office": False,
        },
        ctx.duration("message_queue", 30, 70),
        visible=False,
    )
