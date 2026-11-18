"""Check and freeze the playable catalog and its links to the resolver."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game import catalog
from game.world_cases import FILES
from game.world_institutions import BODIES
from game.world_regional import LAYERS

MECHANISMS = [
    (
        "申请与递交",
        "world_projects",
        "permit",
        "permit_done",
        "项目主管收到前置材料",
        ["P02", "P03"],
    ),
    (
        "签署、拒签与暂缓",
        "world_office",
        "authority",
        "coord_sign",
        "岗位或有效限期授权支持签署",
        ["S04", "P01"],
    ),
    (
        "承诺及到期",
        "world_social",
        "commitment",
        "promise_due",
        "已送达的明确承诺",
        ["K02", "K15"],
    ),
    (
        "修订与复制",
        "world_projects",
        "revise",
        "revise",
        "原版本可查并已比对",
        ["K01", "P01"],
    ),
    (
        "建立分期任务",
        "world_projects",
        "offer",
        "mobilize",
        "方案、授权、前置和时段齐备",
        ["P01", "P02", "P03"],
    ),
    (
        "执行与资源结算",
        "world_projects",
        "offer",
        "construction_done",
        "已预留资金、班组和施工范围",
        ["P01", "P03"],
    ),
    (
        "延期与重排",
        "world_projects",
        "cancel_reservation",
        "offer_review",
        "限定未进场且未支付的阶段",
        ["K03", "K09"],
    ),
    (
        "检查验收整改",
        "world_projects",
        "passage",
        "passage_stage",
        "已建成实物及相应检查记录",
        ["K03", "P01"],
    ),
    (
        "邀约与回复",
        "world_social",
        "invite",
        "invite_end",
        "已有指定邀请及回复期",
        ["L04", "N12"],
    ),
    ("会面与出入", "world", "travel", "arrive", "可达地点及必要预约", ["L05", "L06"]),
    (
        "说话与试探",
        "world_social",
        "speak",
        "speak",
        "已到场且具有实际听者",
        ["L04", "L09"],
    ),
    (
        "条件协商",
        "world_projects",
        "propose",
        "offer_review",
        "存在可行范围与财政答复",
        ["K09", "N06"],
    ),
    (
        "主观关系更新",
        "world_office",
        "consult",
        "actor_response",
        "本人实际收到有出处的答复",
        ["N10", "N18"],
    ),
    (
        "人情与回请",
        "world_office",
        "favour",
        "favour_done",
        "先有当事人知道的具体帮助和回请",
        ["N03", "N12"],
    ),
    (
        "合作与竞争",
        "world_projects",
        "cooperate",
        "cooperate",
        "道路协作意见及真实岗位候选窗口",
        ["N03", "K08"],
    ),
    (
        "共同暴露",
        "world_social",
        "gift",
        "witness",
        "实际双方交接、签收和取证",
        ["N17", "K13"],
    ),
    (
        "空缺与考察",
        "world_career",
        "nominate",
        "appointment_review",
        "实际离任、任期与履职资格",
        ["N04", "K10"],
    ),
    (
        "任命、调任与交接",
        "world_career",
        "career_exit",
        "handover",
        "有权机构办理与接收人交接",
        ["K10", "K16"],
    ),
    (
        "预算和工作组",
        "world_projects",
        "offer",
        "mobilize",
        "年度资金、季度上限和实际容量",
        ["K09", "P03"],
    ),
    (
        "授权与撤销",
        "world_office",
        "authority",
        "auth_expire",
        "签署范围、有效主体和截止",
        ["N10", "P01"],
    ),
    (
        "消息送达",
        "world_office",
        "inquire",
        "actor_response",
        "合法接收渠道和实际收件人",
        ["N10", "N11"],
    ),
    (
        "转述与失真",
        "world_social",
        "speak",
        "relay",
        "传播者实际听到原话",
        ["N15", "N17"],
    ),
    (
        "查证及反证",
        "world_projects",
        "evidence",
        "evidence",
        "独立来源、日期和范围",
        ["K01", "K06"],
    ),
    (
        "澄清与认知更新",
        "world_social",
        "clarify",
        "clarified",
        "曾有真实接触及签收渠道",
        ["K11", "K12"],
    ),
    (
        "线索与主张",
        "world_career",
        "refer",
        "acquire",
        "有可交付独立材料",
        ["K13", "K14"],
    ),
    (
        "保全与取得链",
        "world_social",
        "copy_note",
        "copy_note",
        "实际原件可访问",
        ["N19", "K14"],
    ),
    (
        "程序推进",
        "world_career",
        "review",
        "review_done",
        "核查机构取得材料并完成受理",
        ["N05", "N19"],
    ),
    (
        "制度认定",
        "world_career",
        "hearing",
        "finding_done",
        "已有来源、证词与听取意见程序",
        ["N05", "N17"],
    ),
    (
        "家庭计划",
        "world_social",
        "family_plan",
        "family_train",
        "培训和照护使用真实日历",
        ["N14", "N15"],
    ),
    (
        "休息与照护",
        "world_social",
        "rest",
        "rest",
        "用时与日内恢复上限",
        ["K16", "L07"],
    ),
    (
        "不可逆意图确认",
        "world_social",
        "confirm_note",
        "confirm_note",
        "同一持有物、位置、版本与确认时点",
        ["K13", "K14"],
    ),
    (
        "生涯终局",
        "world_career",
        "career_exit",
        "handover",
        "既有状态及实际程序结果",
        ["K16", "END01", "END02"],
    ),
]

ROUTES = [
    (
        ["propose", "offer", "cancel_reservation"],
        "工程前置不齐时无法接受拨款条款",
        ["B40-ADM", "B40-OFF", "B40-WIN"],
    ),
    (
        ["compare", "delegate", "reply"],
        "未获独立材料时修订仍须保留不确定",
        ["B40-VER", "B40-MSG"],
    ),
    (
        ["speak", "clarify", "invite"],
        "未到场无法产生当面原话",
        ["B40-OFF", "B40-MSG", "B40-WIN"],
    ),
    (
        ["family_plan", "rest", "career_exit"],
        "工作重叠时照护安排可能落空",
        ["B40-REC", "B40-WIN"],
    ),
    (
        ["observe", "evidence", "passage"],
        "缺少合格检查记录不得批准开放",
        ["B40-VER", "B40-ADM", "B40-MSG"],
    ),
    (
        ["cooperate", "favour", "nominate"],
        "合作不授予岗位资格",
        ["B40-CASE", "B40-OBJ"],
    ),
    (
        ["mentor", "mentor_channel", "inquire"],
        "未取得更新材料的建议可以过时",
        ["B40-VER", "B40-MSG"],
    ),
    (
        ["copy_note", "take_note", "confirm_note"],
        "未接触实体物品无法阅读原件",
        ["B40-MSG", "B40-CASE"],
    ),
    (
        ["refer", "review", "hearing"],
        "私人猜测单独不能形成岗位处分",
        ["B40-ADM", "B40-VER", "B40-REC"],
    ),
    (
        ["nominate", "cross_review", "career_exit"],
        "没有实际空缺时无法提出任命",
        ["B40-ADM", "B40-MSG", "B40-CASE"],
    ),
]


def manifest():
    all_refs = {
        key
        for table in (
            catalog.STARTS,
            catalog.LOCATIONS,
            catalog.PEOPLE,
            catalog.PROJECTS,
            catalog.CASES,
            catalog.ENDINGS,
        )
        for key in table
    }
    rule_modules = list((ROOT / "game").glob("world*.py"))
    source = "\n".join(p.read_text() for p in rule_modules)
    entries = []
    for i, (name, module, action, callback, precondition, refs) in enumerate(
        MECHANISMS, 1
    ):
        if not set(refs) <= all_refs:
            raise ValueError(refs)
        if f'"{action}"' not in source or f'"{callback}"' not in source:
            raise ValueError((action, callback))
        entries.append(
            {
                "id": f"M{i:02}",
                "name": name,
                "handler": "game." + module,
                "schema_version": "action/1",
                "rule_version": catalog.VERSION,
                "trigger_types": [action, callback],
                "precondition": precondition,
                "entities": refs,
                "input": "kind + validated action args",
                "output": "committed effects + source-linked event",
                "dedupe_policy": "command_id + expected_revision; task token or state precondition",
                "offline_source": f"game/{module}.py",
            }
        )
    scenes = []
    for (key, info), (routes, counter, bindings) in zip(
        catalog.SCENES.items(), ROUTES, strict=True
    ):
        if (
            not set(info["cases"]) <= set(catalog.CASES)
            or not info["place"] in catalog.LOCATIONS
        ):
            raise ValueError(key)
        scenes.append(
            {
                **info,
                "routes": routes,
                "counterexample": counter,
                "parameter_references": bindings,
            }
        )
    return {
        "schema_version": "content-manifest/1",
        "version": catalog.VERSION,
        "title": "局中事",
        "world": "江岚省／临江市／澄川县",
        "source": "V4.0 补充规则及继承的世界合同；虚构世界，本地简体中文模板",
        "starts": list(catalog.STARTS.values()),
        "locations": list(catalog.LOCATIONS.values()),
        "actors": list(catalog.PEOPLE.values()),
        "projects": list(catalog.PROJECTS.values()),
        "cases": [
            {
                **row,
                "review_owner": FILES[key][0],
                "evidence_prefixes": list(FILES[key][1]),
                "completion_evidence_prefixes": list(FILES[key][2]),
                "new_submission": "case_file",
                "checkpoint": "case_intake / case_verdict",
                "three_quarter_regression": "tests/test_world_v4.py::test_all_cases_can_receive_new_material_after_three_quarters",
            }
            for key, row in catalog.CASES.items()
        ],
        "scenes": scenes,
        "arcs": list(catalog.ARCS.values()),
        "endings": list(catalog.ENDINGS.values()),
        "mechanisms": entries,
        "institutions": BODIES,
        "regional_pools": [
            {
                "rank": rank,
                "office": layer[0],
                "contact": layer[1],
                "authority": layer[2],
                "jurisdictions": list(layer[3]),
                "unit": layer[4],
                "capacity": 3,
            }
            for rank, layer in LAYERS.items()
        ],
        "verification": {
            "arcs": "tests/test_world_v4.py::test_six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes",
            "instances": "tests/test_world_v4.py::test_institution_can_appoint_a_new_identity_without_copying_private_beliefs",
            "regional": "tests/test_cross_system_routes.py::test_separate_jurisdictions_compete_for_a_single_real_pool",
            "historical_routes": "tests/test_cross_system_routes.py",
        },
        "visibility": "本目录为开发者覆盖索引；玩家界面只读取实时 PlayerView。",
    }


if __name__ == "__main__":
    destination = ROOT / "CONTENT_MANIFEST.json"
    output = json.dumps(manifest(), ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        if destination.read_text() != output:
            raise SystemExit("CONTENT_MANIFEST.json 与注册内容不一致")
    else:
        destination.write_text(output)
