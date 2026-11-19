"""Confirmed fictional attempts. An intention cannot create a missing possession."""

from .world_common import action, know


def options(d):
    return [
        action(
            "present_item",
            "试图出示一件受限物品",
            "这会构成一次当场举动。意图、实际持有物、旁人观察各自记录。",
            "原地行动",
            "现场举动",
            {"item": "restricted"},
        )
    ]


def act(d, kind, args, ctx):
    if kind != "present_item":
        return False
    from .catalog import LOCATIONS
    from .world import present

    # No registered item instance in this world pack has this property.
    # The player's claim is insufficient to give the person an item or authority.
    if args["item"] != "restricted":
        raise ValueError("所指物品未登记。")
    record = ctx.emit(
        "你没有持有这件物品，出示未能完成。",
        title="未能出示",
        kind="AttemptUnfulfilled",
    )
    for observer in LOCATIONS[d["location"]]["people"]:
        if not present(d, observer, d["location"]):
            continue
        seen = ctx.emit(
            "在场者看到你作了一个动作，没有看到被出示的物品。",
            title="在场观察",
            actor=observer,
            visible=False,
            refs=(record,),
        )
        know(d, observer, seen, "我看见当事人作了一个动作；没有看见物品。")
    return True


def complete(d, kind, args, ctx):
    return False
