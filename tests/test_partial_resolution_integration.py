"""Integration tests for partial resolution in command rendering."""

from datetime import datetime

import pytest

from mcp_guide.render.template import render_template
from mcp_guide.utils.file_discovery import FileInfo


class TestPartialResolutionIntegration:
    """Test that partials resolve correctly relative to template files."""

    @pytest.mark.asyncio
    async def test_partial_resolves_relative_to_template(self, tmp_path):
        """Test partial resolution uses template's parent directory, not commands root."""
        # Create directory structure:
        # commands/
        #   info/
        #     project.mustache (template)
        #   _partials/
        #     _project.mustache (partial)

        commands_dir = tmp_path / "commands"
        info_dir = commands_dir / "info"
        partials_dir = commands_dir / "_partials"

        info_dir.mkdir(parents=True)
        partials_dir.mkdir(parents=True)

        # Create partial
        partial_file = partials_dir / "_project.mustache"
        partial_file.write_text("Project: {{project_name}}")

        # Create template that includes partial using relative path
        template_file = info_dir / "project.mustache"
        template_file.write_text("""---
type: user/information
includes:
  - ../_partials/project
---
{{>project}}
""")

        # Render template
        from mcp_guide.utils.template_context import TemplateContext

        context = TemplateContext({"project_name": "test-project"})
        file_info = FileInfo(
            path=template_file,
            size=100,
            content_size=50,
            mtime=datetime.now(),
            name="project",
        )

        result = await render_template(
            file_info=file_info,
            base_dir=template_file.parent,
            project_flags={},
            context=context,
        )

        assert result is not None
        assert "Project: test-project" in result.content

    @pytest.mark.asyncio
    async def test_deeply_nested_template_partial_resolution(self, tmp_path):
        """Test partial resolution works for templates in deeply nested directories."""
        # Create structure:
        # commands/
        #   workflow/
        #     phase/
        #       check.mustache (template)
        #   _partials/
        #     _status.mustache (partial)

        commands_dir = tmp_path / "commands"
        phase_dir = commands_dir / "workflow" / "phase"
        partials_dir = commands_dir / "_partials"

        phase_dir.mkdir(parents=True)
        partials_dir.mkdir(parents=True)

        # Create partial
        partial_file = partials_dir / "_status.mustache"
        partial_file.write_text("Status: {{status}}")

        # Create template (needs to go up 2 levels: phase -> workflow -> commands)
        template_file = phase_dir / "check.mustache"
        template_file.write_text("""---
type: workflow/phase
includes:
  - ../../_partials/status
---
{{>status}}
""")

        # Render template
        from mcp_guide.utils.template_context import TemplateContext

        context = TemplateContext({"status": "checking"})
        file_info = FileInfo(
            path=template_file,
            size=100,
            content_size=50,
            mtime=datetime.now(),
            name="check",
        )

        result = await render_template(
            file_info=file_info,
            base_dir=template_file.parent,
            project_flags={},
            context=context,
        )

        assert result is not None
        assert "Status: checking" in result.content
