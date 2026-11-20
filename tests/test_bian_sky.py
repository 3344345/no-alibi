"""Original 4.2.2 archive fingerprints, divergent classroom routes and later echoes."""

from functools import cache

import pytest

from game.chronicle import Book, Branch, ChronicleStore, Command
from game.store import GameStore
from game.witness_bian_sky import LOST, RETURNED
from game.witness_late import CHAPTERS


CAST_422 = (
    "tan_sitong zhan_tianyou sun_yatsen chen_duxiu gu_zhenghong shen_junru zhang_xueliang "
    "minnie_vautrin chongqing_talks shanghai_prices liu_qingshan lushan_peng lin_zhao bian "
    "entrance_exam hu_fuming xiaogang yuan_geng deng_xiaoping southern_tour shang_aiyun "
    "gao deng xu_zhiyong jiang_yanyong"
)


def walk(store, view, path):
    for key in path.split():
        view = store.choose(
            view["id"],
            Command(
                command_id="new-" + str(view["revision"]),
                revision=view["revision"],
                choice=key,
            ),
        )
    return view


@pytest.mark.parametrize(
    "short,old,checksum,legacy_end,entry,mark",
    [
        (
            "f3",
            "ask_colleagues ask_for_leave use_leave",
            "ae8d40334c57d029a0b7f69d39fcb122c4958079407a8bf2f1b77e9a41c2cabd",
            "take_home_duty",
            "sky_live_on",
            RETURNED,
        ),
        (
            "f4",
            "ask_colleagues join_request wait_responsible stay_for_reply",
            "92cef3fb343f74cddeb7baff6f2a92c04408110ac5b9b2ae2537b87698bce45a",
            "request_account",
            "sky_years",
            LOST,
        ),
    ],
)
def test_archives_before_the_expansion_keep_both_ways_forward(
    tmp_path, short, old, checksum, legacy_end, entry, mark
):
    archive = {
        "format": "juzhongshi-chronicle/3",
        "campaign": "witness",
        "start_chapter": "witness_bian",
        "id": short * 16,
        "name": "白粉笔",
        "chapters": ["witness_" + c for c in CAST_422.split()],
        "commands": [
            {"revision": i, "command_id": f"old-{i}", "choice": key}
            for i, key in enumerate(old.split())
        ],
        "checksum": checksum,
    }
    store = ChronicleStore(GameStore(tmp_path / "career"))
    v = store.restore(archive)
    branch = store.fork(v["id"], Branch(revision=v["revision"]))
    assert walk(store, v, legacy_end)["chapter"]["id"] != "witness_bian"
    expanded = walk(store, branch, entry)
    assert expanded["scene"]["id"] == "sky_yard" and mark in expanded["marks"]
    assert ({RETURNED, LOST} - {mark}).isdisjoint(expanded["marks"])


@pytest.mark.parametrize(
    "prefix,middle,early,late,forbidden,payout",
    [
        (
            "sky_if sky_move sky_swap sky_own sky_work sky_pay sky_private sky_guest_out",
            "sky_touchlesson sky_hall sky_both_names sky_say",
            True,
            "sky_work_end",
            "sky_visit_end",
            "两位老师",
        ),
        (
            "sky_fact sky_feel sky_wrap sky_start_silent sky_chairs sky_second sky_two sky_guest_in",
            "sky_window sky_court sky_lend sky_go",
            False,
            "sky_visit_end",
            "sky_work_end",
            "扶门",
        ),
        (
            "sky_fact sky_move sky_pause_lamp sky_own sky_work sky_roster sky_two sky_guest_in",
            "sky_touchlesson sky_hall sky_hall_small sky_say",
            False,
            "sky_school_end",
            "sky_work_end",
            "归来",
        ),
        (
            "sky_if sky_feel sky_return_lamp sky_start_silent sky_chairs sky_open_seat sky_private sky_guest_out",
            "sky_window sky_court sky_home sky_go",
            False,
            "sky_family_end",
            "sky_visit_end",
            "门内",
        ),
    ],
)
def test_long_route_persists_and_earlier_decisions_unlock_distinct_lives(
    tmp_path, prefix, middle, early, late, forbidden, payout
):
    store = ChronicleStore(GameStore(tmp_path / "career"))
    v = walk(
        store, store.create("夜课", "witness", "witness_bian"), "sky_long " + prefix
    )
    assert v["scene"]["id"] == "sky_fog"
    if early:
        assert "那一肚子气" in v["scene"]["body"]
    portable = store.export(v["id"])
    second = ChronicleStore(GameStore(tmp_path / "portable"))
    assert second.restore(portable) == v
    last = walk(second, v, middle)
    assert last["scene"]["id"] == "sky_last"
    assert forbidden not in [c["id"] for c in last["scene"]["choices"]]
    ending = walk(second, last, late)
    assert ending["chapter"]["id"] != "witness_bian"
    assert payout in ending["journal"][-1]["marks"][0]


def test_twenty_year_arc_has_four_acts_on_every_route():
    chapter = next(ch for ch in CHAPTERS if ch["id"] == "witness_bian")
    nodes = Book([chapter], "witness").scene_maps[0]

    @cache
    def endings(key):
        if key == "END":
            return {(0, ())}
        scene = nodes[key]
        act = scene.title.split(" · ")[0]
        return {
            (count + 1, (act,) + tuple(x for x in acts if x != act))
            for choice in scene.choices
            for count, acts in endings(choice.next)
        }

    assert len([key for key in nodes if key.startswith("sky_")]) == 16
    assert all(
        acts == ("一幕", "二幕", "三幕", "四幕") and turns >= 12
        for turns, acts in endings("sky_day")
    )
