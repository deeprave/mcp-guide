"""Tests for workflow state branching in the status command template.

Tests the three required states:
  - workflow disabled (no workflow context)
  - workflow enabled but no state received yet
  - workflow enabled with state available

Also tests the monitoring-setup bootstrap guidance.
"""

import pytest

from mcp_guide.render.context import TemplateContext
from mcp_guide.render.renderer import render_template_content

_STATUS_TEMPLATE_PATH = "src/mcp_guide/templates/_commands/status.mustache"
_MONITORING_SETUP_PATH = "src/mcp_guide/templates/_workflow/monitoring-setup.mustache"


def _load_template_body(path: str) -> str:
    """Load a mustache template body, stripping the YAML frontmatter block."""
    from pathlib import Path

    text = Path(path).read_text()
    if text.startswith("---"):
        end = text.index("---", 3)
        return text[end + 3 :].lstrip("\n")
    return text


class TestStatusWorkflowDisabled:
    """Status template when the workflow flag is disabled (no workflow context)."""

    @pytest.mark.anyio
    async def test_disabled_says_tracking_is_disabled(self) -> None:
        """Disabled workflow should state plainly that tracking is disabled."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({})  # No 'workflow' key → disabled
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "disabled" in rendered.lower()

    @pytest.mark.anyio
    async def test_disabled_omits_send_file_content(self) -> None:
        """Disabled workflow should NOT instruct the agent to use send_file_content."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "send_file_content" not in rendered


class TestStatusWorkflowEnabledNoState:
    """Status template when workflow is enabled but no state received yet."""

    @pytest.mark.anyio
    async def test_enabled_no_state_shows_setup_guidance(self) -> None:
        """Enabled-but-no-state should tell the agent to send the workflow file."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "send_file_content" in rendered

    @pytest.mark.anyio
    async def test_enabled_no_state_mentions_not_received(self) -> None:
        """Enabled-but-no-state message should say the file has not been received."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "not yet been received" in rendered


class TestStatusWorkflowEnabledWithState:
    """Status template when workflow is enabled and state is available."""

    @pytest.mark.anyio
    async def test_enabled_with_state_renders_state_section(self) -> None:
        """Enabled-with-state renders the workflow-status partial area (no setup guidance)."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml", "phase": "implementation"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        # The setup guidance should NOT appear — the state section renders instead
        assert "not yet been received" not in rendered
        assert "disabled" not in rendered.lower()

    @pytest.mark.anyio
    async def test_enabled_with_state_omits_setup_guidance(self) -> None:
        """Enabled-with-state should NOT show send_file_content setup guidance."""
        body = _load_template_body(_STATUS_TEMPLATE_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml", "phase": "implementation"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "send_file_content" not in rendered


class TestMonitoringSetupBootstrap:
    """monitoring-setup template bootstrap guidance for missing workflow files."""

    @pytest.mark.anyio
    async def test_includes_bootstrap_content_for_missing_file(self) -> None:
        """monitoring-setup should specify bootstrap content with phase: discussion."""
        body = _load_template_body(_MONITORING_SETUP_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "phase: discussion" in rendered

    @pytest.mark.anyio
    async def test_includes_blank_issue_line(self) -> None:
        """monitoring-setup bootstrap content must include an explicit blank issue: line."""
        body = _load_template_body(_MONITORING_SETUP_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "issue:" in rendered

    @pytest.mark.anyio
    async def test_existing_file_guidance_present(self) -> None:
        """monitoring-setup should still include send_file_content instruction."""
        body = _load_template_body(_MONITORING_SETUP_PATH)
        context = TemplateContext({"workflow": {"file": ".guide.yaml"}, "tool_prefix": ""})
        result = await render_template_content(body, context)
        assert result.success
        rendered, _, _ = result.value
        assert "send_file_content" in rendered
