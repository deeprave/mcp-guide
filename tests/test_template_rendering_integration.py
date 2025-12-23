"""Integration tests for template rendering with project flags."""

from unittest.mock import AsyncMock, Mock, patch

from mcp_guide.models import Project
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.utils.template_renderer import render_template_content


class TestTemplateRenderingWithFlags:
    """Test template rendering with project flags integration."""

    async def test_template_renders_with_phase_tracking_flag_true(self) -> None:
        """Test that template content renders when phase-tracking flag is true."""
        # Create a simple template with conditional content using dict format
        template_content = """{{#project.project_flags.phase-tracking}}
Phase tracking is enabled!
{{/project.project_flags.phase-tracking}}"""

        # Mock project with phase-tracking flag enabled
        mock_project = Project(
            name="test-project", categories={}, collections={}, project_flags={"phase-tracking": True}
        )

        # Mock session
        mock_session = Mock()
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get template context with project flags
            context = await get_template_contexts()

            # Render template
            result = render_template_content(template_content, context)

            # Verify content is rendered
            assert result.success
            rendered_content = result.value
            assert "Phase tracking is enabled!" in rendered_content

    async def test_template_does_not_render_with_phase_tracking_flag_false(self) -> None:
        """Test that template content does not render when phase-tracking flag is false."""
        # Create a simple template with conditional content
        template_content = """{{#project.flags.phase-tracking}}
Phase tracking is enabled!
{{/project.flags.phase-tracking}}"""

        # Mock project with phase-tracking flag disabled
        mock_project = Project(
            name="test-project", categories={}, collections={}, project_flags={"phase-tracking": False}
        )

        # Mock session
        mock_session = Mock()
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get template context with project flags
            context = await get_template_contexts()

            # Render template
            result = render_template_content(template_content, context)

            # Verify content is not rendered
            assert result.success
            rendered_content = result.value
            assert "Phase tracking is enabled!" not in rendered_content
            # Should be empty or just whitespace
            assert rendered_content.strip() == ""

    async def test_template_does_not_render_with_missing_flag(self) -> None:
        """Test that template content does not render when flag is missing."""
        # Create a simple template with conditional content
        template_content = """{{#project.flags.phase-tracking}}
Phase tracking is enabled!
{{/project.flags.phase-tracking}}"""

        # Mock project without phase-tracking flag
        mock_project = Project(
            name="test-project",
            categories={},
            collections={},
            project_flags={},  # No flags
        )

        # Mock session
        mock_session = Mock()
        mock_session.get_project = AsyncMock(return_value=mock_project)

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            # Get template context with project flags
            context = await get_template_contexts()

            # Render template
            result = render_template_content(template_content, context)

            # Verify content is not rendered
            assert result.success
            rendered_content = result.value
            assert "Phase tracking is enabled!" not in rendered_content
            # Should be empty or just whitespace
            assert rendered_content.strip() == ""
