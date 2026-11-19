"""A case file can outlive its project phase. Every new submission needs a source."""

from .catalog import DAY, PEOPLE, PROJECTS
from .world_common import action, case, know, visible_doc

# Document patterns address only records actually received by this player.
# Conditions select evidence of resolution, not a verdict about historical truth.
FILES = {
    "K01": (
        "N08",
        ("D01-", "OBS-site"),
        ("D01-r2",),
        "核对进度口径，注明尚未查实的部分",
    ),
    "K02": (
        "N10",
        ("receipt-", "POST-", "REPLY-N10"),
        ("receipt-", "POST-"),
        "核实承诺的收件、履行与截止",
    ),
    "K03": (
        "N08",
        ("P01-", "D16-", "OBS-site"),
        ("P01-inspect-", "P01-stage-"),
        "核对南渠检查与当期施工窗口",
    ),
    "K04": (
        "N09",
        ("P03-", "REPLY-N09"),
        ("P03-stage-", "P03-permit"),
        "核对医院的分区与门诊安排",
    ),
    "K05": (
        "N12",
        ("INVITE-", "D05-", "REPLY-N12"),
        ("D05-attend", "D05-explain"),
        "分别核对婉拒时刻与实际到场",
    ),
    "K06": (
        "N18",
        ("D01-detail", "OBS-site", "REPLY-N18"),
        ("D01-detail", "OBS-site"),
        "按实际取得渠道核实现场材料",
    ),
    "K07": (
        "N10",
        ("D07-", "REPLY-N10", "advice-N12"),
        ("D07-contact",),
        "核对旧联系人与当前职责交接单",
    ),
    "K08": (
        "N03",
        ("D08-", "POS-", "P02-", "INTER-"),
        ("D08-division", "POS-"),
        "区分道路协作责任与岗位竞争",
    ),
    "K09": (
        "N06",
        ("D06-", "BUD-", "P01-stage", "P02-stage", "P03-stage"),
        ("BUD-",),
        "核对财政确认版本和获配的范围",
    ),
    "K10": (
        "N04",
        ("POS-", "D10-office", "INTER-"),
        ("POS-",),
        "核对空缺、考察与接任决定",
    ),
    "K11": (
        "N15",
        ("SPEECH-", "RELAY-", "CLARIFY-"),
        ("CLARIFY-",),
        "区分原话、转述与已送达的澄清",
    ),
    "K12": (
        "N10",
        ("advice-", "D12-check", "D07-"),
        ("D12-check", "D07-contact"),
        "核对导师所用联系人与材料日期",
    ),
    "K13": (
        "N19",
        ("NB-copy-", "NB-ver-", "NB-reader-"),
        ("NB-ver-", "NB-copy-"),
        "区分笔记的记录、猜测与独立来源",
    ),
    "K14": (
        "N19",
        ("NB-copy-", "NB-ver-", "NB-reader-"),
        ("NB-copy-", "NB-ver-", "NB-reader-"),
        "查找原件以外实际留存的材料",
    ),
    "K15": (
        "N14",
        ("FAM-", "CLARIFY-", "SPEECH-"),
        ("FAM-reply", "CLARIFY-"),
        "查明谁作出家庭承诺并核对实际日程",
    ),
    "K16": (
        "N10",
        ("HR-", "CARE-", "FAM-"),
        ("HR-transfer", "CARE-plan", "FAM-reply"),
        "核对照护、留任与岗位交接的范围",
    ),
}


def available(d, key):
    _, patterns, _, _ = FILES[key]
    stage_prefixes = tuple(
        project + "-" for project, spec in PROJECTS.items() if spec["stage_case"] == key
    )
    return [doc for doc in d["docs"].values() if doc["id"].startswith(patterns + stage_prefixes)]


def options(d):
    if d["location"] != "L01":
        return []
    rows = []
    for key, row in sorted(d["cases"].items()):
        owner, _, _, topic = FILES[key]
        if row.get("pending_review"):
            continue
        seen = set(row.get("reviewed_docs", []))
        possible = [doc for doc in available(d, key) if doc["id"] not in seen]
        if possible:
            choices = [
                {"label": doc["title"], "value": doc["id"]}
                for doc in sorted(possible, key=lambda x: x["id"])
            ]
            field = {
                "name": "document",
                "label": "递交哪一份材料",
                "type": "select",
                "options": choices,
                "default": choices[0]["value"],
                "required": True,
            }
            rows.append(
                action(
                    "case_file",
                    "补交材料 · " + row["title"],
                    "向"
                    + PEOPLE[owner]["name"]
                    + "递交新取得的有效版本，"
                    + topic
                    + "。",
                    "签收后复核",
                    "案卷办理",
                    {"case": key, "mode": "submit"},
                    [field],
                )
            )
        if row["status"] not in ("dormant", "resolved"):
            rows.append(
                action(
                    "case_file",
                    "暂存待查 · " + row["title"],
                    "附上当前出处，保留以后补件的入口。原承诺、工程与程序仍照常履行。",
                    "即时登记",
                    "案卷办理",
                    {"case": key, "mode": "shelve"},
                )
            )
    return rows


def act(d, k, p, ctx):
    if k != "case_file":
        return False
    key = p["case"]
    row = d["cases"][key]
    owner, _, _, topic = FILES[key]
    if p["mode"] == "shelve":
        ref = ctx.emit(
            "现有来件暂存待查：" + topic + "。",
            title=row["title"] + " · 暂存",
            refs=(row["history"][-1]["ref"],),
        )
        case(d, key, "dormant", ref, "暂存期间保留原件与到期责任。")
        return True
    doc = d["docs"][p["document"]]
    if doc not in available(d, key) or doc["id"] in row.get("reviewed_docs", []):
        raise ValueError("这份材料不能构成新的复核依据。")
    ref = ctx.emit(
        "已递交" + doc["title"] + "，等待指定收件人签收。",
        title=row["title"] + " · 补件",
        refs=tuple(doc["refs"]),
    )
    row["pending_review"] = ref
    ctx.schedule(
        "case_intake",
        {"case": key, "document": doc["id"], "request": ref, "owner": owner},
        ctx.duration("message_queue", 15, 45),
        title=row["title"] + " · 补件送达",
    )
    return True


def complete(d, k, p, ctx):
    if k not in ("case_intake", "case_verdict"):
        return False
    key = p["case"]
    row = d["cases"][key]
    if row.get("pending_review") != p["request"]:
        return True
    doc = d["docs"].get(p["document"])
    if not doc:
        row.pop("pending_review", None)
        ctx.emit("指定材料当前不能调取。", title=row["title"] + " · 退件")
        return True
    if k == "case_intake":
        old = row["status"]
        ref = ctx.emit(
            PEOPLE[p["owner"]]["name"] + "签收了" + doc["title"] + "。",
            title=row["title"] + " · 取得新材料",
            actor=p["owner"],
            refs=(p["request"], *doc["refs"]),
        )
        know(d, p["owner"], ref, doc["body"])
        case(
            d,
            key,
            "active",
            ref,
            ("依据新的材料重开。" if old in ("resolved", "dormant") else "补件已签收。")
            + FILES[key][3]
            + "。",
        )
        ctx.schedule(
            "case_verdict",
            {**p, "receipt": ref},
            ctx.duration("admin", 20, 50),
            title=row["title"] + " · 范围复核",
        )
        return True
    row.pop("pending_review", None)
    row.setdefault("reviewed_docs", []).append(doc["id"])
    supports = doc["id"].startswith(FILES[key][2])
    text = (
        f"当前问题在《{doc['title']}》覆盖范围内完成核对。其余命题另行查证。"
        if supports
        else f"《{doc['title']}》只能支持其中一部分，仍待其他独立材料。"
    )
    ref = ctx.emit(
        text, title=row["title"] + " · 复核回函", actor=p["owner"], refs=(p["receipt"],)
    )
    case(d, key, "resolved" if supports else "contested", ref, text)
    visible_doc(
        d,
        "CASE-" + key + "-" + str(len(row["reviewed_docs"])),
        row["title"] + "复核回函",
        text,
        p["owner"],
        doc["scope"],
        ref=ref,
    )
    return True
