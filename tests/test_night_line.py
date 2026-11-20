"""Long route depth, gated endings and an archive fingerprint from the 4.2.2 release."""

from functools import cache

import pytest

from game.chronicle import Book, Branch, ChronicleStore, Command
from game.store import GameStore
from game.witness_deng import CHAPTERS
from game.witness_night_line import SCENES


CHAPTER_ID = "witness_deng_xiaoping"
PREVIOUS_CAST = (
    "tan_sitong zhan_tianyou sun_yatsen chen_duxiu gu_zhenghong shen_junru zhang_xueliang "
    "minnie_vautrin chongqing_talks shanghai_prices liu_qingshan lushan_peng lin_zhao bian "
    "entrance_exam hu_fuming xiaogang yuan_geng deng_xiaoping southern_tour shang_aiyun "
    "gao deng xu_zhiyong jiang_yanyong"
)


def play(store, view, choices):
    for key in choices.split():
        view = store.choose(view["id"], Command(revision=view["revision"],
                            command_id=f"move-{view['revision']}", choice=key))
    return view


def test_original_register_save_can_branch_to_full_night_broadcast(tmp_path):
    original = {
        "format": "juzhongshi-chronicle/3", "campaign": "witness", "start_chapter": CHAPTER_ID,
        "id": "f1" * 16, "name": "四月的留存",
        "chapters": ["witness_" + actor for actor in PREVIOUS_CAST.split()],
        "commands": [
            {"revision": i, "command_id": f"before-{i}", "choice": key}
            for i, key in enumerate(("open_meeting", "pay_window", "both"))
        ],
        "checksum": "df51fa1acbd0b4b3f672a98412dc9b8073d5d912462ac8dac0e5354c6de7e131",
    }
    store = ChronicleStore(GameStore(tmp_path / "game.db"))
    restored = store.restore(original)
    assert restored["scene"]["id"] == "register"
    branch = store.fork(restored["id"], Branch(revision=3))
    assert play(store, restored, "numbered")["scene"]["id"] == "april_return"
    assert play(store, branch, "night_line")["scene"]["id"] == "night_switchboard"


def test_every_night_route_has_five_acts_and_at_least_22_decisions():
    book = Book([CHAPTERS[1]], "witness")
    scenes = book.scene_maps[0]

    @cache
    def walks(key):
        if key == "END":
            return {(0, ())}
        item = scenes[key]
        assert item.id.startswith("night_")
        act = item.title.split(" · ")[0]
        result = set()
        for choice in item.choices:
            for length, acts in walks(choice.next):
                result.add((length + 1, (act,) + tuple(a for a in acts if a != act)))
        return result

    assert {acts for _, acts in walks("night_switchboard")} == {("一幕", "二幕", "三幕", "四幕", "五幕")}
    assert min(length for length, _ in walks("night_switchboard")) >= 22
    assert len({s["id"] for s in SCENES}) == 37


@pytest.mark.parametrize(
    ("first", "turn", "ending", "other", "early_echo"),
    [
        ("public stall punch cook kin child hand leave letters together music board match",
         "morning hold ride money year names away coach", "double", None, "第一晚替陌生人"),
        ("private laugh sheet draw whole father cut quiet wheel stand closed caller quiet",
         "families visitor wages people count advance home coach", "clockwork", "double", "那个号码一次也没有"),
        ("public airtime sheet date kin father hand voice letters together closed caller repeat",
         "martial keep record name visit own keep along", "record", None, "修鞋摊"),
    ],
)
def test_three_worlds_persist_and_pay_off(tmp_path, first, turn, ending, other, early_echo):
    store = ChronicleStore(GameStore(tmp_path / "game.db"))
    v = play(store, store.create("留声", "witness", CHAPTER_ID), "night_line " + first)
    assert v["scene"]["id"] == "night_cabinet"
    keys = turn.split()
    v = play(store, v, " ".join(keys[:-1]))
    assert early_echo in v["scene"]["body"]
    v = play(store, v, keys[-1])
    options = [c["id"] for c in v["scene"]["choices"]]
    if other:
        assert other not in options
    portable = store.export(v["id"])
    resumed = ChronicleStore(GameStore(tmp_path / "second.db"))
    assert resumed.restore(portable) == v
    finished = play(resumed, v, ending)
    assert finished["chapter"]["id"] != CHAPTER_ID
    assert finished["journal"][-1]["marks"][0].startswith("结局 · ")
