"""The chronology of saves made before the first in-file chapter manifests."""

FAMILY_11 = (
    "may_fourth",
    "shanghai_workers",
    "mukden_september",
    "nantao_refuge",
    "gold_yuan",
    "river_grain",
    "school_album",
    "household_field",
    "june_workshop",
    "factory_minutes",
    "school_ground",
)
WITNESS_10 = (
    "witness_chen_duxiu",
    "witness_shen_junru",
    "witness_zhang_xueliang",
    "witness_liu_qingshan",
    "witness_bian",
    "witness_entrance_exam",
    "witness_xiaogang",
    "witness_deng_xiaoping",
    "witness_gao",
    "witness_deng",
)
WITNESS_8 = tuple(
    ch for ch in WITNESS_10 if ch not in ("witness_liu_qingshan", "witness_xiaogang")
)


def legacy_books(book):
    # These editions did not record a manifest. Try the latest original edition
    # first when neither the starting actor nor the recorded history distinguishes them.
    orders = (FAMILY_11,) if book.campaign == "family" else (WITNESS_10, WITNESS_8)
    supported = [order for order in orders if set(order) <= book.indices.keys()]
    if supported:
        return [book.in_order(order) for order in supported]
    # Custom local books can use different identifiers. Never substitute a
    # partially installed official book for a missing historical edition.
    if any(set(order).intersection(book.indices) for order in orders):
        return []
    return [book]
