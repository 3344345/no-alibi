"""A distinct registered project and owner can use the whole delivery workflow."""

from unittest.mock import patch

import pytest

from game import catalog, world
from tests.test_world_v4 import D, Play


@patch.dict(catalog.PROJECTS)
def test_substituted_project_and_owner_from_registration_through_next_phase(
    monkeypatch,
):
    project, owner = "P90", "N90"
    monkeypatch.setitem(
        catalog.PEOPLE,
        owner,
        {
            **catalog.PEOPLE["N07"],
            "id": owner,
            "name": "龚研",
        },
    )
    catalog.PROJECTS[project] = {
        **catalog.PROJECTS["P02"],
        "id": project,
        "name": "档案馆通道",
        "deliverable": "档案馆开放入口",
        "owner": owner,
        "permit_action": "申请档案馆开放会签",
    }
    del catalog.PROJECTS["P02"]
    g = Play().go("L03")
    action = next(
        a
        for a in world.actions(g.d)
        if a["kind"] == "permit" and a["args"]["project"] == project
    )
    assert action["label"] == "申请档案馆开放会签"
    g.do("propose", plan="A").wait(180)
    with pytest.raises(ValueError):
        g.do("offer", offer="OF-1", choice="accept")
    g.do("offer", offer="OF-1", choice="withdraw")
    g.do("permit", project=project).do("permit", project="P03").wait(2 * D)
    g.do("propose", plan="A").wait(180)
    g.do("offer", offer="OF-2", choice="accept").wait(10 * D)
    g.do("stage_check", project=project).wait(300)
    material = g.d["projects"][project]
    assert material["opened"] and "P02" not in g.d["projects"]
    approval = next(e for e in g.log if e["id"] == material["approvals"][-1])
    assert approval["actor"] == owner and approval["refs"] == [
        material["approvals"][-2]
    ]
    g.do("new_phase", project=project)
    assert g.d["projects"][project]["stage_number"] == 2
    assert g.d["projects"]["P03"]["stage_number"] == 1
