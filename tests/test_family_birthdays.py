"""《两回生日》在家书的正常时间线、未走选支的旧档与分线中的承接。"""

import pytest

from game.chronicle import Branch, ChronicleStore, Command
from game.store import GameStore


def move(store, view, key):
    assert any(c["id"] == key for c in view["scene"]["choices"])
    return store.choose(
        view["id"],
        Command(
            revision=view["revision"], command_id=f"step-{view['revision']}", choice=key
        ),
    )


def route(store, view, keys):
    for key in keys.split():
        view = move(store, view, key)
    return view


def travel(store, view, chapter):
    for _ in range(100):
        if view["chapter"]["id"] == chapter:
            return view
        view = move(store, view, view["scene"]["choices"][0]["id"])
    pytest.fail(f"未抵达 {chapter}")


@pytest.mark.parametrize(
    ("wedding", "heirloom", "absent", "refuge", "unlocked", "other", "shop", "result"),
    [
        (
            "east_bed carry_spoon own_door",
            "use_spoon",
            "show_fruit",
            "paid_round ask_back",
            "first_round",
            "sleep_over",
            "invite_workers open_counter",
            "枕头换来的一扇窗",
        ),
        (
            "west_bed turn_fruit two_teas",
            "show_fruit",
            "use_spoon",
            "name_borrower little_first",
            "sleep_over",
            "first_round",
            "let_sleep keep_bed",
            "窗外歇火的一晚",
        ),
    ],
)
def test_1919_household_choices_change_the_1937_visit_and_1948_scenes(
    tmp_path, wedding, heirloom, absent, refuge, unlocked, other, shop, result
):
    store = ChronicleStore(GameStore(tmp_path / "story.db"))
    start = store.create("两回生日")
    v = route(store, start, f"two_birthdays {wedding} send_proof")
    v = move(store, travel(store, v, "nantao_refuge"), "two_birthdays")
    assert absent not in {c["id"] for c in v["scene"]["choices"]}
    v = route(store, v, f"{heirloom} {refuge} keep_cloth")
    v = move(store, travel(store, v, "gold_yuan"), "two_birthdays")
    assert other not in {c["id"] for c in v["scene"]["choices"]}
    assert unlocked in {c["id"] for c in v["scene"]["choices"]}
    resumed = ChronicleStore(GameStore(tmp_path / "import.db"))
    assert resumed.restore(store.export(v["id"])) == v
    ending = route(resumed, v, f"{unlocked} {shop}")
    assert ending["scene"]["id"] == "headline"
    assert any(result in mark for mark in ending["marks"])
    assert store.view(start["id"]) == v


def test_published_archive_enters_later_without_imaginary_heirlooms(tmp_path):
    # Captured using the 4.2.2 (4678e05) catalogue and route fingerprints.
    archive = {
        "format": "juzhongshi-chronicle/3",
        "campaign": "family",
        "start_chapter": "may_fourth",
        "chapters": [
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
        ],
        "id": "a6" * 16,
        "name": "五月里",
        "commands": [
            {"revision": i, "command_id": f"old-{i}", "choice": key}
            for i, key in enumerate(("set_sheet", "ask_copyist"))
        ],
        "checksum": "1ab8bd1f63b0b6451c123ae01fc5d28f90058d9ddd02f243ecd654d87d7aa59b",
    }
    store = ChronicleStore(GameStore(tmp_path / "restored.db"))
    old = store.restore(archive)
    assert old["scene"]["id"] == "flag" and store.export(old["id"]) == archive
    branch = store.fork(old["id"], Branch(revision=2))
    v = move(store, travel(store, branch, "nantao_refuge"), "two_birthdays")
    assert {c["id"] for c in v["scene"]["choices"]} == {
        "take_to_kitchen",
        "stay_at_stove",
    }
    v = route(store, v, "take_to_kitchen hire_girl little_first keep_cloth")
    v = move(store, travel(store, v, "gold_yuan"), "two_birthdays")
    assert {c["id"] for c in v["scene"]["choices"]} == {"measure_room", "measure_bed"}
    v = route(store, v, "measure_room pay_daughter keep_bed")
    assert "两回生日·窗外歇火的一晚" in v["marks"]
    assert store.export(old["id"]) == archive
