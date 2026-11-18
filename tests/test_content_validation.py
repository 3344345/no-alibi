"""A corrupt catalog must stop a release build before packaging."""

import pytest

from game import catalog, world_templates
from scripts.content_manifest import manifest


@pytest.mark.parametrize(
    ("table", "key", "field", "invalid"),
    [
        (catalog.LOCATIONS, "L01", "access", "unregistered"),
        (catalog.STARTS, "S01", "creditor", "N99"),
        (catalog.ENDINGS, "END01", "resume_policy", "unknown_policy"),
        (catalog.PROJECTS, "P01", "id", "P03"),
        (catalog.PROJECTS, "P02", "stage_case", "K99"),
        (catalog.PROJECTS, "P02", "plan_shares", {"A": [100, -2]}),
        (catalog.PROJECTS, "P02", "permit_action", " "),
    ],
)
def test_invalid_content_cannot_be_packaged(monkeypatch, table, key, field, invalid):
    monkeypatch.setitem(table[key], field, invalid)
    with pytest.raises(ValueError, match=key):
        manifest()


def test_missing_offline_template_cannot_be_packaged(monkeypatch):
    monkeypatch.delitem(world_templates.DENIALS, "L07")
    with pytest.raises(ValueError, match=r"L07.*模板"):
        manifest()


def test_ambiguous_opening_project_is_rejected(monkeypatch):
    monkeypatch.setitem(catalog.PROJECTS["P02"], "opening_passage", True)
    with pytest.raises(ValueError, match="唯一的开局通路"):
        manifest()
