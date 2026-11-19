"""Pure construction of eligible model menus. AI output can only select a registered option."""

from ai.advisor import case_menu, npc_menu


def npc_request(domain, ctx, actor_id):
    actor = domain["actors"][actor_id]
    beliefs = actor["beliefs"]
    prior = "genesis/" + actor_id
    claim = beliefs.get(prior, "请按职责核对已经收到的材料。")
    sources = [r for r in beliefs if not r.startswith("genesis/")]
    choices = [{"key": "routine", "text": claim, "refs": [prior]}]
    if sources:
        choices.append(
            {
                "key": "verify",
                "text": "请一起核对已收材料的日期和范围。",
                "refs": [sources[-1]],
            }
        )
    menu = npc_menu(actor_id, beliefs, actor["goals"], choices)
    selected = ctx.suggest(menu, "routine")
    return next((c.text for c in menu.choices if c.key == selected), claim)


def followup(domain, ctx, actor_id, fallback):
    case_id = "K08" if actor_id == "N03" else "K13"
    case = domain["cases"].get(case_id)
    if not case or not case["history"]:
        return fallback
    latest = case["history"][-1]
    sources = {latest["ref"]: latest["text"]}
    choices = [
        {"key": "meeting", "text": fallback, "refs": [latest["ref"]]},
        {
            "key": "material",
            "text": "来函请你带上已经取得的材料，在会面时逐项核对来源。",
            "refs": [latest["ref"]],
        },
    ]
    menu = case_menu(case_id, sources, choices)
    selected = ctx.suggest(menu, "meeting")
    return next(c.text for c in menu.choices if c.key == selected)
