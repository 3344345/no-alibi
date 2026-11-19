"""Smoke-test all four optional model roles using a new fictional career."""

from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai.advisor import Endpoint, narrative_menu, parser_menu
from game import proposals
from game.store import GameStore


def verify(endpoint, folder):
    store = GameStore(folder / "test.sqlite3")
    view = store.create("S04", "林岑", "0.500000", "classic")
    world = view["world_id"]
    opening = view

    def submit(kind, **args):
        nonlocal view
        revision = view["revision"]
        view = store.execute(world, f"step-{revision}", revision, kind, args)

    submit("travel", location="L03")
    submit("advance", minutes=view["busy"]["due"] - view["minute"])
    submit("cooperate")
    submit("advance", minutes=view["busy"]["due"] - view["minute"])
    with store._db(snapshot=True) as db:
        domain = json.loads(store._world(db, world)["projection"])["domain"]
    results = {}

    class LiveSuggestions:
        def suggest(self, menu, fallback):
            start = monotonic()
            selected, failed = endpoint.choose(menu)
            legal = {row.key for row in menu.choices}
            results[menu.role] = {
                "accepted": bool(selected) and not failed and set(selected) <= legal,
                "selected": len(selected),
                "seconds": round(monotonic() - start, 2),
            }
            return selected[0] if selected and not failed else fallback

    live = LiveSuggestions()
    live.suggest(parser_menu("暂时先别给出书面答复", opening["actions"]), None)
    proposals.npc_request(domain, live, "N03")
    proposals.followup(domain, live, "N03", "请核对那份联署意见。")
    live.suggest(narrative_menu(view), None)
    print(
        json.dumps(
            {"model": endpoint.model, "roles": results}, ensure_ascii=False, indent=2
        )
    )
    roles = {"parse", "npc_propose", "case_propose", "narrate"}
    return (
        set(results) == roles
        and all(r["accepted"] for r in results.values())
        and view == store.view(world)
        and store.replay(world)
    )


if __name__ == "__main__":
    provider = Endpoint.from_env()
    if provider is None:
        sys.exit("请先设置 JUZHONGSHI_AI_URL 和 JUZHONGSHI_AI_MODEL。")
    with TemporaryDirectory(prefix="jzs-model-check-") as temp:
        sys.exit(0 if verify(provider, Path(temp)) else 1)
