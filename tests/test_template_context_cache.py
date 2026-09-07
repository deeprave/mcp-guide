"""Template cache composition through real sessions, flags and task state."""

import platform
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from mcp_guide.agent_detection import AgentInfo
from mcp_guide.models import Category
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.render.cache import TemplateContextCache, get_template_contexts
from mcp_guide.workflow.schema import WorkflowState
from tests.helpers import create_bound_test_session, create_unbound_test_session


@pytest.fixture
async def session(runtime):
    runtime.configuration_service().config_file.write_text("projects: {}\nfeature_flags: {}\n")
    return await create_bound_test_session(runtime, "context-project")


@pytest.mark.anyio
async def test_complete_context_contains_real_project_category_and_system(session):
    project = await session.get_project()
    await session.save_project(replace(project, categories={"docs": Category(dir="./docs", patterns=["*.md"])}))
    context = await get_template_contexts(session)
    assert context["project"]["name"] == "context-project"
    assert context["project"]["project_flags"] == {}
    assert context["project"]["project_flag_values"] == []
    assert context["projects"]["projects"][0]["current"] is True
    assert context["server"]["os"] == platform.system()
    assert context["server"]["platform"] == platform.platform()
    assert context["server"]["python_version"] == platform.python_version()
    assert context["@"] == "@"
    assert await get_template_contexts(session) is context
    category = (await get_template_contexts(session, "docs"))["category"]
    assert category["name"] == "docs"
    assert category["dir"] == "./docs/"
    assert category["patterns"][0]["value"] == "*.md"
    missing = (await get_template_contexts(session, "missing"))["category"]
    assert missing["name"] == ""
    assert missing["patterns"] == []


@pytest.mark.anyio
async def test_unbound_context_does_not_create_or_borrow_a_project(runtime):
    unbound = create_unbound_test_session(runtime)
    for cache in (TemplateContextCache(), unbound.template_cache):
        context = await cache.get_template_contexts()
        assert context["project"]["name"] == ""
        assert context["project"]["categories"] == []
    assert unbound.bound_root_path is None
    assert unbound.project is None


@pytest.mark.anyio
@pytest.mark.parametrize("error", [ValueError, AttributeError])
async def test_project_read_failure_uses_empty_context(session, monkeypatch, error):
    # Inject an unavailable configuration boundary; normal fixtures cannot reliably cause it.
    async def unavailable():
        raise error("Project unavailable")

    monkeypatch.setattr(session, "get_project", unavailable)
    context = await get_template_contexts(session)
    assert context["project"]["name"] == ""
    assert context["project"]["categories"] == []


def test_transient_timestamps_are_fresh_consistent_and_formatted(monkeypatch):
    import time

    ticks = iter([1_700_000_000_000_000_000, 1_700_000_001_000_000_000])
    monkeypatch.setattr(time, "time_ns", lambda: next(ticks))
    cache = TemplateContextCache()
    contexts = [cache.get_transient_context(), cache.get_transient_context()]
    assert contexts[1]["timestamp"] - contexts[0]["timestamp"] == 1
    for context in contexts:
        assert context["timestamp"] == context["timestamp_ns"] / 1_000_000_000
        assert context["timestamp_ms"] == context["timestamp_ns"] / 1_000_000
        expected = datetime.fromtimestamp(context["timestamp"], tz=timezone.utc)
        assert context["now_utc"] == {
            "date": expected.strftime("%Y-%m-%d"),
            "day": expected.strftime("%A"),
            "time": expected.strftime("%H:%M"),
            "tz": "+0000",
            "datetime": expected.strftime("%Y-%m-%d %H:%M:%SZ"),
        }
        local = context["now"]
        assert local["date"] and local["day"] and local["time"] and local["tz"]
        parsed_local = datetime.strptime(local["datetime"], "%Y-%m-%d %H:%M:%S%z")
        assert parsed_local.replace(tzinfo=None) == datetime.fromtimestamp(context["timestamp"])


@pytest.mark.anyio
@pytest.mark.parametrize("enabled,available", [(True, True), (True, False), (False, False)])
async def test_openspec_context_uses_global_state_not_task_local_availability(session, runtime, enabled, available):
    await runtime.feature_flags().set(
        "openspec-state", {"validated": str(available).lower(), "version": "1.10.0", "checked": "100.0"}
    )
    if enabled:
        await session.project_flags().set("openspec", True)
        task = session.task_manager.get_task_by_type(OpenSpecTask)
        assert task is not None
        assert task.is_available() is None
    context = await get_template_contexts(session)
    if not enabled:
        assert context["openspec"] is False
        return
    openspec = context["openspec"]
    assert openspec["available"] is available
    assert openspec["version"] == "1.10.0"
    assert openspec["changes"] == []
    assert openspec["show"] is None
    assert openspec["status"] is None
    assert openspec["has_version"]("1.9.0", lambda text: text) is True
    assert openspec["has_version"]("1.11.0", lambda text: text) is False


@pytest.mark.anyio
@pytest.mark.parametrize(
    "name,normalised,prefix,handoff,membership",
    [
        ("Kiro CLI", "q-dev", "@", True, {"is_q_dev", "is_kiro"}),
        ("pi-mcp-guide", "pi", None, False, {"is_pi"}),
        ("Custom Agent", "custom-agent", "/", False, set()),
    ],
)
async def test_agent_context_reports_membership_and_handoff(session, name, normalised, prefix, handoff, membership):
    session.agent_info = AgentInfo(name=name, normalized_name=normalised, version="1.0.0", prompt_prefix=prefix)
    agent = (await get_template_contexts(session))["agent"]
    assert agent["class"] == normalised
    assert agent["prefix"] == (prefix or "")
    assert agent["has_handoff"] is handoff
    assert {key for key, value in agent.items() if key.startswith("is_") and value} == membership


@pytest.mark.anyio
@pytest.mark.parametrize(
    "phase,issue,consent,next_phase,entry,exit",
    [
        ("implementation", "test-issue", True, "check", True, False),
        ("review", "test-issue", True, "discussion", False, True),
        ("exploration", "explor-test", True, None, False, True),
        ("planning", "test-issue", {"planning": ["entry", "exit"], "check": ["entry"]}, "implementation", True, True),
        ("implementation", "test-issue", False, "check", False, False),
    ],
    ids=["default-entry", "default-exit-wrap", "unordered-exploration", "custom-consent", "disabled-consent"],
)
async def test_workflow_context_combines_state_phase_order_and_consent(
    session, phase, issue, consent, next_phase, entry, exit
):
    await session.project_flags().set("workflow", True)
    await session.project_flags().set("workflow-consent", consent)
    session.task_manager.set_cached_data("workflow_state", WorkflowState(phase=phase, issue=issue))
    workflow = (await get_template_contexts(session))["workflow"]
    assert workflow["phase"] == phase
    assert workflow["issue"] == issue
    assert workflow["next"] == ({"value": next_phase} if next_phase else None)
    assert workflow["consent"]["entry"] is entry
    assert workflow["consent"]["exit"] is exit
    for name in ("discussion", "planning", "implementation", "check", "review"):
        assert workflow[name] is True
    assert workflow["phases"]["exploration"]["ordered"] is False
    assert "next" not in workflow["phases"]["exploration"]
    assert workflow["issue_is_exploratory"] is False
    if isinstance(consent, dict):
        assert workflow["consent"]["check"] == {"entry": True, "exit": False, "any": True}
    elif consent:
        assert workflow["consent"]["implementation"] == {"entry": True, "exit": False, "any": True}
        assert workflow["consent"]["review"] == {"entry": False, "exit": True, "any": True}
        assert workflow["consent"]["discussion"] == {"entry": False, "exit": False, "any": False}
    else:
        assert all(not workflow["consent"][name]["any"] for name in workflow["phases"])
