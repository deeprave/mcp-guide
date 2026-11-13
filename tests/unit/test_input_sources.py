"""Dynamic elicitation choice sources."""

import pytest

from mcp_guide.input_sources import _SOURCES, prepare_form_sources, workflow_phase_names
from mcp_guide.render.context import TemplateContext


def _phase_form() -> dict:
    return {
        "workflow-phase": {
            "message": "Choose the phase to enter.",
            "fallback": "render",
            "schema": {
                "type": "object",
                "properties": {"phase": {"type": "string", "source": "workflow-phases"}},
                "required": ["phase"],
            },
        }
    }


def _workflow_context(*phases: str, current: str | None = None) -> TemplateContext:
    workflow: dict = {"phase_list": list(phases)}
    if current is not None:
        workflow["phase"] = current
    return TemplateContext({"workflow": workflow})


def test_phase_choices_omit_the_active_phase_and_explicit_inputs():
    """Enabled phases become the choice list, without the phase already in effect."""
    forms = prepare_form_sources(
        _phase_form(),
        _workflow_context("discussion", "planning", "review", current="planning"),
        [],
    )

    assert forms["workflow-phase"]["schema"]["properties"]["phase"]["enum"] == ["discussion", "review"]
    assert "source" not in forms["workflow-phase"]["schema"]["properties"]["phase"]

    supplied = prepare_form_sources(
        _phase_form(),
        _workflow_context("discussion", "planning", current="discussion"),
        ["planning"],
    )
    assert supplied == {}

    explicit_keyword = prepare_form_sources(
        _phase_form(),
        _workflow_context("discussion", "planning", current="planning"),
        [],
        {"phase": "planning"},
    )
    assert explicit_keyword["workflow-phase"]["schema"]["properties"]["phase"]["enum"] == ["discussion"]


def test_phase_form_is_omitted_when_no_other_phase_is_enabled():
    """A project already on its only enabled phase is not asked to choose it again."""
    forms = prepare_form_sources(
        _phase_form(),
        _workflow_context("discussion", current="discussion"),
        [],
    )

    assert forms == {}


def test_workflow_phase_names_preserve_declared_order_and_mapping_fallback():
    """The shared phase helper provides one canonical normalised phase sequence."""
    assert workflow_phase_names({"phase_list": [{"value": "discussion"}, "planning", "planning"]}) == [
        "discussion",
        "planning",
    ]
    assert workflow_phase_names({"phases": {"discussion": {}, "review": {}}}) == ["discussion", "review"]


def _project_form(source: str, field: str = "name") -> dict:
    return {
        "choose": {
            "message": "Choose one.",
            "fallback": "render",
            "schema": {
                "type": "object",
                "properties": {field: {"type": "string", "source": source}},
                "required": [field],
            },
        }
    }


def _project_context() -> TemplateContext:
    return TemplateContext(
        {
            "project": {
                "categories": [{"name": "docs"}, {"name": "code"}, {"name": "docs"}],
                "collections": [{"name": "guidelines", "categories": ["docs"]}],
            }
        }
    )


def test_project_categories_and_collections_become_enum_choices():
    """Project names are offered as distinct choices and the source marker is removed."""
    categories = prepare_form_sources(_project_form("project-categories"), _project_context())
    collections = prepare_form_sources(_project_form("project-collections"), _project_context())

    assert categories["choose"]["schema"]["properties"]["name"] == {"type": "string", "enum": ["docs", "code"]}
    assert collections["choose"]["schema"]["properties"]["name"] == {"type": "string", "enum": ["guidelines"]}


def test_worktree_inventory_offers_linked_paths_only():
    context = TemplateContext(
        {"worktree": {"path": "/client/root", "inventory": {"paths": ["/client/root", "/client/linked"]}}}
    )

    prepared = prepare_form_sources(_project_form("worktree-inventory", field="worktree_path"), context)

    assert prepared["choose"]["schema"]["properties"]["worktree_path"] == {
        "type": "string",
        "enum": ["/client/linked"],
    }


def test_project_source_form_retains_choices_for_supplied_keywords():
    """A supplied keyword retains dynamic choices for generic URI validation."""
    form = _project_form("project-categories")

    assert prepare_form_sources(form, _project_context(), ["docs"]) == {}
    supplied = prepare_form_sources(form, _project_context(), [], {"name": "docs"})
    assert supplied["choose"]["schema"]["properties"]["name"]["enum"] == ["docs", "code"]
    assert prepare_form_sources(form, TemplateContext({"project": {"categories": []}})) == {}
    assert prepare_form_sources(form, TemplateContext({})) == {}


@pytest.mark.parametrize(
    "keyword",
    [None, "", "   ", "docs", 0, False],
    ids=["null", "empty", "blank", "text", "zero", "false"],
)
def test_keywords_retain_sourced_forms_for_validation(keyword):
    """Supplied keywords retain source choices for generic validation."""
    prepared = prepare_form_sources(_project_form("project-categories"), _project_context(), [], {"name": keyword})

    assert bool(prepared)


def test_skill_forms_resolve_sources_without_positional_arguments():
    """Skills pass no positional arguments, so any source applies to their forms."""
    form = _project_form("project-categories", field="category")

    prepared = prepare_form_sources(form, _project_context(), (), {})

    assert prepared["choose"]["schema"]["properties"]["category"]["enum"] == ["docs", "code"]


def test_unknown_source_is_left_as_free_text():
    """An unrecognised source marker is removed rather than delivered to the client."""
    prepared = prepare_form_sources(_project_form("no-such-source"), _project_context())

    assert prepared["choose"]["schema"]["properties"]["name"] == {"type": "string"}


def test_supplied_value_resolves_its_choices_for_validation(monkeypatch):
    """A supplied value resolves its source choices for generic validation."""
    lookups = []
    monkeypatch.setitem(_SOURCES, "counting", lambda context: lookups.append(context) or ["a"])
    form = {
        "choose": {
            "message": "Choose.",
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string", "source": "counting"}},
                "required": ["name"],
            },
        }
    }

    assert "choose" in prepare_form_sources(form, {}, [], {"name": "a"})
    assert len(lookups) == 1
    assert "choose" in prepare_form_sources(form, {})
    assert len(lookups) == 2
