"""Competing jurisdictional submissions, with a separate authorised reviewer pool."""

from .catalog import DAY
from .world_common import action, know, visible_doc

LAYERS = {
    2: ("县域统筹", "N22", "临江市协调处", ("澄川县", "望宁县"), "联合核查人日"),
    3: ("市级协调", "N22", "临江市协调处", ("澄川县", "望宁县"), "跨县技术复核人日"),
    4: ("省级统筹", "N23", "江岚省审议组", ("临江市", "云田市"), "跨市档案审查人日"),
    5: ("中央议题", "N24", "专题材料处", ("江岚省", "岐川省"), "专题资料核查人日"),
}


def setup(d):
    d["regional"] = {}
    for idx, (level, actor, body, names, unit) in LAYERS.items():
        d["regional"][str(idx)] = {
            "body": body,
            "contact": actor,
            "level": level,
            "unit": unit,
            "capacity": 3,
            "reserved": 0,
            "requests": {
                n: {"requested": 2, "served": 0, "state": "未报送"} for n in names
            },
            "cycle": 0,
            "status": "未交接",
            "received": [],
        }


def start(d, rank, ctx, ref):
    if rank < 2:
        return
    box = d["regional"][str(rank)]
    box["status"] = "汇总在途"
    box["cycle"] += 1
    box["received"] = []
    for i, name in enumerate(box["requests"]):
        row = box["requests"][name]
        row.update(requested=2, served=0, state="已发申请")
        dispatch = ctx.emit(
            f"{name}提交两人日的{box['unit']}申请。",
            title="辖区报送",
            actor=box["contact"],
            visible=False,
            refs=(ref,),
        )
        ctx.schedule(
            "regional_intake",
            {"rank": rank, "name": name, "origin": dispatch, "cycle": box["cycle"]},
            ctx.duration("message_queue", 20 + i * 15, 30 + i * 10),
            title="辖区汇总预计送达",
        )


def options(d):
    rank = d["career"]["rank"]
    if rank < 2 or d["location"] != "L01":
        return []
    box = d["regional"][str(rank)]
    if box["status"] != "待协调" or len(box["received"]) != 2:
        return []
    names = list(LAYERS[rank][3])
    return [
        action(
            "regional_allocate",
            label,
            f"两个辖区各申请 2 人日，当前审批池只有 3 人日。{desc}",
            "经受理后占用真实时段",
            "跨辖区",
            {"choice": ch},
        )
        for ch, label, desc in [
            ("first", "优先" + names[0], names[1] + "须压缩一人日的审查范围。"),
            ("second", "优先" + names[1], names[0] + "须压缩一人日的审查范围。"),
            ("stage", "两地各办第一阶段", "暂留最后一人日，两地都只完成部分查核。"),
        ]
    ]


def act(d, k, p, ctx):
    if k != "regional_allocate":
        return False
    rank = d["career"]["rank"]
    box = d["regional"][str(rank)]
    row = box["requests"]
    names = LAYERS[rank][3]
    amounts = {"first": (2, 1), "second": (1, 2), "stage": (1, 1)}[p["choice"]]
    cuts = dict(zip(names, amounts, strict=True))
    ref = ctx.emit(
        "已将具体协调范围送至" + box["body"] + "，等待其确认共享时段。",
        title="辖区协调送审",
        refs=tuple(box["received"]),
    )
    box["status"] = "待核准"
    ctx.schedule(
        "regional_decide",
        {"rank": rank, "cycle": box["cycle"], "alloc": cuts, "ref": ref},
        ctx.duration("admin", 30, 90),
        title="辖区受理答复",
    )
    return True


def complete(d, k, p, ctx):
    if k not in ("regional_intake", "regional_decide", "regional_finish"):
        return False
    rank = p["rank"]
    box = d["regional"][str(rank)]
    if p["cycle"] != box["cycle"]:
        return True
    if k == "regional_intake":
        name = p["name"]
        row = box["requests"][name]
        row["state"] = "已送达"
        ref = ctx.emit(
            f"{name}申请 {row['requested']} 人日。现有共同审批时段共 {box['capacity']} 人日。",
            title="取得辖区汇总",
            actor=box["contact"],
            refs=(p["origin"],),
        )
        box["received"].append(ref)
        row["ref"] = ref
        visible_doc(
            d,
            f"REG-{rank}-{box['cycle']}-{name}",
            name + " · 核查申请",
            f"{name}申请两人日，仅覆盖本次报送的议题。",
            box["contact"],
            box["unit"],
            ref=ref,
        )
        if len(box["received"]) == 2:
            box["status"] = "待协调"
        return True
    if k == "regional_decide":
        amount = sum(p["alloc"].values())
        if amount + box["reserved"] > box["capacity"] or any(
            x > box["requests"][n]["requested"] for n, x in p["alloc"].items()
        ):
            box["status"] = "待协调"
            ctx.emit("本轮无法容纳所报范围，退回重议。", title="辖区受理")
            return True
        ref = ctx.emit(
            box["body"] + "核准本轮范围，各辖区分别收到办理份额。",
            title="共享时段确认",
            actor=box["contact"],
            refs=(p["ref"],),
        )
        box["reserved"] += amount
        box["status"] = "核查中"
        for name, n in p["alloc"].items():
            row = box["requests"][name]
            row["allocated"] = n
            row["state"] = "全项核查" if n == row["requested"] else "缩小阶段范围"
            ctx.schedule(
                "regional_finish",
                {
                    "rank": rank,
                    "cycle": box["cycle"],
                    "name": name,
                    "amount": n,
                    "ref": ref,
                },
                n * DAY,
                title=name + "阶段核查归还时段",
            )
        return True
    name = p["name"]
    row = box["requests"][name]
    n = p["amount"]
    row["served"] += n
    box["reserved"] -= n
    row["state"] = "本期完成" if n == row["requested"] else "未完成部分留待后续"
    ref = ctx.emit(
        f"{name}已实际完成 {n} 人日；{row['state']}。",
        title="跨辖区核查回执",
        actor=box["contact"],
        refs=(p["ref"],),
    )
    know(d, box["contact"], ref, row["state"])
    if not box["reserved"]:
        box["status"] = "已交付"
    return True


def validate(d):
    for box in d["regional"].values():
        if not 0 <= box["reserved"] <= box["capacity"]:
            raise ValueError("跨辖区共享时段超出授权。")
        for row in box["requests"].values():
            if not 0 <= row["served"] <= row["requested"]:
                raise ValueError("辖区用量超出提交范围。")
