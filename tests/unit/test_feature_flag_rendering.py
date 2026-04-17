"""Tests for feature flag rendering with FeatureValue wrappers."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.render.cache import TemplateContextCache
from mcp_guide.render.context import TemplateContext
from mcp_guide.result import Result


@pytest.mark.anyio
async def test_project_context_renders_wrapped_flag_values_for_display():
    """Display-oriented flag lists should use FeatureValue display formatting."""
    cache = TemplateContextCache()

    mock_session = Mock()
    mock_session.get_project = AsyncMock(
        return_value=Mock(
            name="demo",
            key="demo-key",
            hash="demo-hash",
            categories={},
            collections={},
            project_flags={
                "content-style": FeatureValue("plain"),
                "workflow": FeatureValue(["discussion", "implementation"]),
                "workflow-consent": FeatureValue({"implementation": ["entry", "exit"]}),
            },
        )
    )

    mock_feature_flags = Mock()
    mock_feature_flags.list = AsyncMock(return_value={"autoupdate": FeatureValue(True)})
    mock_session.feature_flags.return_value = mock_feature_flags

    with (
        patch("mcp_guide.session.get_session", AsyncMock(return_value=mock_session)),
        patch("mcp_guide.session.list_all_projects", AsyncMock(return_value=Result.ok({"projects": {}}))),
        patch("mcp_guide.models.resolve_all_flags", AsyncMock(return_value={"autoupdate": FeatureValue(True)})),
        patch("mcp_guide.mcp_context.resolve_project_path", AsyncMock(return_value="/tmp/project")),
        patch("mcp_guide.feature_flags.utils.get_resolved_flag_value", AsyncMock(return_value=None)),
    ):
        context = await cache._build_project_context()

    assert [{"key": item["key"], "value": item["value"]} for item in context["project"]["project_flag_values"]] == [
        {"key": "content-style", "value": "plain"},
        {"key": "workflow", "value": "['discussion', 'implementation']"},
        {"key": "workflow-consent", "value": "{'implementation': ['entry', 'exit']}"},
    ]
    assert [{"key": item["key"], "value": item["value"]} for item in context["feature_flag_values"]] == [
        {"key": "autoupdate", "value": "true"}
    ]
    assert [{"key": item["key"], "value": item["value"]} for item in context["flag_values"]] == [
        {"key": "autoupdate", "value": "true"}
    ]
    assert context["project"]["project_flags"]["content-style"] == FeatureValue("plain")
    assert context["project"]["project_flags"]["workflow"] == FeatureValue(["discussion", "implementation"])
    assert context["project"]["project_flags"]["workflow-consent"] == FeatureValue(
        {"implementation": ["entry", "exit"]}
    )


@pytest.mark.anyio
async def test_project_context_preserves_plain_workflow_structures_for_non_display_consumers():
    """Derived workflow context should expose plain dict/boolean structures for templates."""
    cache = TemplateContextCache()

    mock_session = Mock()
    mock_session.get_project = AsyncMock(
        return_value=Mock(
            name="demo",
            key="demo-key",
            hash="demo-hash",
            categories={},
            collections={},
            project_flags={},
        )
    )
    mock_session.feature_flags.return_value = Mock(list=AsyncMock(return_value={}))

    resolved_flags = {
        "workflow": FeatureValue(["discussion", "planning", "implementation", "check", "review"]),
        "workflow-consent": FeatureValue({"planning": ["entry"], "review": ["exit"]}),
    }

    with (
        patch("mcp_guide.session.get_session", AsyncMock(return_value=mock_session)),
        patch("mcp_guide.session.list_all_projects", AsyncMock(return_value=Result.ok({"projects": {}}))),
        patch("mcp_guide.models.resolve_all_flags", AsyncMock(return_value=resolved_flags)),
        patch("mcp_guide.mcp_context.resolve_project_path", AsyncMock(return_value="/tmp/project")),
        patch("mcp_guide.feature_flags.utils.get_resolved_flag_value", AsyncMock(return_value=None)),
        patch("mcp_guide.task_manager.get_task_manager") as mock_task_manager,
    ):
        mock_task_manager.return_value.get_cached_data.return_value = None
        context = await cache._build_project_context()

    assert context["workflow"]["discussion"] is True
    assert context["workflow"]["planning"] is True
    assert context["workflow"]["implementation"] is True
    assert context["workflow"]["check"] is True
    assert context["workflow"]["review"] is True
    assert context["workflow"]["phases"]["planning"] == {"enabled": True, "next": "implementation", "ordered": True}
    assert context["workflow"]["consent"]["planning"] == {"entry": True, "exit": False, "any": True}
    assert context["workflow"]["consent"]["review"] == {"entry": False, "exit": True, "any": True}


def test_generic_indexed_list_rendering_remains_unchanged():
    """Non-display list values should still use IndexedList semantics."""
    context = TemplateContext({"items": ["alpha", "beta"]})

    assert context["items"][0]["value"] == "alpha"
    assert context["items"][0]["first"] is True
    assert context["items"][0]["last"] is False
    assert context["items"][1]["value"] == "beta"
    assert context["items"][1]["first"] is False
    assert context["items"][1]["last"] is True
