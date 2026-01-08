"""Utilities for rendering system content (commands, workflow) from docroot directories."""

from pathlib import Path
from typing import Any

from mcp_guide.result import Result
from mcp_guide.utils.file_discovery import discover_category_files
from mcp_guide.utils.template_renderer import render_file_content


async def render_system_content(
    system_dir: Path,
    pattern: str,
    context: Any,
    docroot: Path,
) -> Result[str]:
    """Render content from system directories like _commands or _workflow.

    Args:
        system_dir: Directory containing the system files
        pattern: File pattern to match
        context: Template context for rendering
        docroot: Project docroot for partial resolution

    Returns:
        Result containing rendered content
    """
    try:
        files = await discover_category_files(system_dir, [pattern])
        if not files:
            return Result.failure(f"No files found matching pattern: {pattern}", error_type="not_found")

        file_info = files[0]  # Use first match
        render_result = await render_file_content(file_info, context, system_dir, docroot)

        if render_result.success:
            return Result.ok(render_result.value)
        else:
            return render_result

    except Exception as e:
        return Result.failure(f"Error rendering system content: {e}", error_type="file_error")
