"""Offline lines. Factual templates only render supplied scene, evidence or actor state."""

from .catalog import CASES, ENDINGS, LOCATIONS

EXITS = {
    "L01": "离开办公室前，你合上手头来文。",
    "L02": "你沿实际开放的路线离开工地。",
    "L03": "你离开协调会，已登记的额度和待办仍留在纪要里。",
    "L04": "你向邻座告辞，席上的人可以继续交谈。",
    "L05": "接待处登记了离场。",
    "L06": "你结束本次同行，离开球场。",
    "L07": "你出门时家人的日程继续。",
    "L08": "你告辞离开老宅。",
    "L09": "你向家人告别，本次聚会的其他人仍可留场。",
}
DENIALS = {
    "L01": "当前日程无法返回办公室。",
    "L02": "当前没有可用行程赴工地。",
    "L03": "当前日程无法到协调会。",
    "L04": "这次饭局缺少有效的赴约安排。",
    "L05": "前台没有当前可用的预约。",
    "L06": "本次同行尚未取得预约，或你已有其他安排。",
    "L07": "当前没有空档返家。",
    "L08": "当前无法安排去老宅的行程。",
    "L09": "当前日程无法赴家族聚会。",
}


def scene_line(key, mode):
    row = LOCATIONS[key]
    return {
        "enter": row["description"],
        "wait": row["wait"],
        "leave": EXITS[key],
        "denied": DENIALS[key],
    }[mode]


def reply(claim, mode, task=None):
    if not claim:
        raise ValueError("需要角色已获且愿意公开的依据。")
    if mode == "blocked":
        if not task:
            raise ValueError("缺少实际在办事项。")
        return f"我正在办理{task}，现在不能详谈；此前可以确认的是“{claim}”"
    if mode == "source":
        return (
            "我目前能说明的根据只限于这段本人陈述：“"
            + claim
            + "”其他情况请查直接记录。"
        )
    if mode == "normal":
        return claim
    raise ValueError("未登记的回应类型。")


def case_line(key, status, detail, reopened=False):
    if not detail:
        raise ValueError("缺少已发生的可见情况。")
    prefix = {
        "signal": "收到来件",
        "active": "开始跟进",
        "contested": "口径待核",
        "dormant": "暂存待查",
        "resolved": "本阶段归档",
    }[status]
    if reopened:
        prefix = "据新材料再次跟进"
    return f"{CASES[key]['name']} · {prefix}。{detail}"


def ending_detail(key, reason, docs, open_promises):
    if key not in ENDINGS or not reason:
        raise ValueError("需要合法终局条件和已提交说明。")
    # Only mention a real, retained player copy; the ending never re-creates a lost notebook.
    source = next((row for row in reversed(docs) if row["kind"] == "制度认定"), None)
    if not source:
        source = next(
            (
                row
                for row in reversed(docs)
                if row["id"] in ("P01-opening", "D01-r2")
                or row["id"].startswith("POST-")
            ),
            None,
        )
    if source:
        return reason + " 留存材料中包括《" + source["title"] + "》。", source["refs"]
    return reason + f" 交接时另有 {open_promises} 项约定待处理。", []
