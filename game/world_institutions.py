"""Institutional appointment rights and identity-safe succession."""

from .catalog import PEOPLE, POSITIONS

BODIES = {
    "county": {
        "name": "澄川县任用委员会",
        "contact": "N04",
        "superior": "city",
        "positions": ["POS-C0", "POS-C1", "POS-C2"],
    },
    "city": {
        "name": "临江市任用委员会",
        "contact": "N21",
        "superior": "province",
        "positions": ["POS-M1"],
    },
    "province": {
        "name": "江岚省岗位审议组",
        "contact": "N23",
        "superior": "central",
        "positions": ["POS-P1"],
    },
    "central": {
        "name": "跨辖区议题任用组",
        "contact": "N24",
        "superior": None,
        "positions": ["POS-Z1"],
    },
}


def setup(d):
    d["institutions"] = {
        key: {"secretariat": row["contact"], "delegation": None, "operational": True}
        for key, row in BODIES.items()
    }
    d["successors"] = {}
    d["career"]["candidate_profiles"] = {
        "N07": {"levels": [1], "served": 8, "delivery_records": 2},
        "N03": {"levels": [1, 2, 3], "served": 12, "delivery_records": 3},
    }


def authority(d, pos):
    body = next(k for k, v in BODIES.items() if pos in v["positions"])
    record = d["institutions"][body]
    if record["operational"]:
        return body
    # A vacant appointing body requires the superior's explicitly recorded mandate.
    while BODIES[body]["superior"]:
        body = BODIES[body]["superior"]
        record = d["institutions"][body]
        if record["operational"] and record.get("delegation") == pos:
            return body
    return None


def alternative(d, idx, quarter):
    c = d["career"]
    pos = POSITIONS[idx]
    candidates = ("N03", "N07") if d["flags"].get("cooperate") else ("N07", "N03")
    for who in candidates:
        profile = c["candidate_profiles"][who]
        if (
            idx in profile["levels"]
            and profile["served"] >= pos[2]
            and profile["delivery_records"] >= 2
            and who not in c["positions"].values()
            and who != c.get("departed")
        ):
            return who
    # This reference is a backed nomination file from the institution's qualified external pool.
    return f"candidate/{pos[0]}/{quarter}"


def appoint_person(d, selected, idx, ref, ctx):
    if not selected.startswith("candidate/"):
        return selected
    key = f"R{len(d['successors']) + 1:03}"
    names = ["陶谨言", "顾思澄", "季明岚", "林予初", "闻于青", "孙时安"]
    name = names[len(d["successors"]) % len(names)]
    pos = POSITIONS[idx]
    created = ctx.emit(
        "任用机关核验外部候选档案并为接任人建立独立履职记录。",
        title="继任人建档",
        actor=pos[3],
        refs=(ref,),
    )
    d["successors"][key] = {
        "id": key,
        "name": name,
        "role": pos[1],
        "description": pos[4] + "履职交接",
        "present": False,
        "origin": created,
    }
    d["actors"][key] = {
        "beliefs": {created: "接到本人任职通知，等待交接材料。"},
        "goals": ["接收本岗位公开事项"],
        "resources": {"channel": pos[1]},
        "relations": {
            pos[3]: {
                "trust": 0.4,
                "familiarity": 0.15,
                "dependency": 0.1,
                "competition": 0.2,
                "shared_exposure": 0,
            }
        },
        "plans": ["核实已接收项目的期限"],
        "wake": "收到范围内交接材料",
        "last_acted": None,
    }
    return key


def display(d, key):
    if key == "player":
        return "你"
    return (PEOPLE.get(key) or d["successors"][key])["name"]
