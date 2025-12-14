"""Template rendering utilities for Mustache templates."""

import logging
from typing import Any, Callable, Optional

import chevron

from mcp_core.result import Result
from mcp_guide.tools.tool_constants import INSTRUCTION_FILE_ERROR, INSTRUCTION_VALIDATION_ERROR
from mcp_guide.utils.file_discovery import TEMPLATE_EXTENSION, FileInfo
from mcp_guide.utils.template_context import TemplateContext
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.utils.template_functions import TemplateFunctions


def is_template_file(file_info: FileInfo) -> bool:
    """Check if FileInfo represents a template file.

    Args:
        file_info: FileInfo to check

    Returns:
        True if file has .mustache extension
    """
    return str(file_info.path).endswith(TEMPLATE_EXTENSION)


def _safe_lambda(func: Callable[..., str]) -> Callable[..., str]:
    """Wrap lambda function to handle errors gracefully.

    Logs the full exception and returns a concise, user-safe error string that
    includes the exception type to aid debugging.
    """

    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log full traceback for diagnostics
            logging.exception("Error while evaluating template lambda")
            # Return a user-friendly error string with exception type preserved
            return f"[Template Error ({type(e).__name__}): {e}]"

    return wrapper


def render_template_content(
    content: str,
    context: TemplateContext,
    file_path: str = "<template>",
    transient_fn: Optional[Callable[[TemplateContext], TemplateContext]] = None,
) -> Result[str]:
    """Render template content with context.

    Args:
        content: Template content to render
        context: Template context data
        file_path: File path for error reporting
        transient_fn: Optional function to add transient data to context

    Returns:
        Result with rendered content or error
    """
    try:
        # Apply transient function if provided
        render_context = transient_fn(context) if transient_fn else context

        # Create template functions and inject into context with error handling
        functions = TemplateFunctions(render_context)
        template_context = render_context.new_child(
            {
                "format_date": _safe_lambda(functions.format_date),
                "truncate": _safe_lambda(functions.truncate),
                "highlight_code": _safe_lambda(functions.highlight_code),
            }
        )

        # Render template with Chevron (TemplateContext works as ChainMap)
        rendered = chevron.render(content, template_context)  # type: ignore[arg-type]
        return Result.ok(rendered)

    except Exception as e:
        return Result.failure(
            error=f"Template rendering failed for {file_path}: {str(e)}",
            error_type="template_error",
            exception=e,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )


def render_file_content(file_info: FileInfo, context: TemplateContext | None = None) -> Result[str]:
    """Render file content, applying template rendering if needed.

    Args:
        file_info: FileInfo with content to render
        context: Template context (if None, pass through content unchanged)

    Returns:
        Result with rendered content or original content
    """
    if file_info.content is None:
        return Result.failure(
            error=f"File content not loaded: {file_info.path}",
            error_type="content_error",
            instruction=INSTRUCTION_FILE_ERROR,
        )

    # Pass through non-template files unchanged
    if not is_template_file(file_info) or context is None:
        return Result.ok(file_info.content)

    # Render template files
    result = render_template_content(file_info.content, context, str(file_info.path))

    # Update file size if rendering succeeded
    if result.is_ok() and result.value is not None:
        file_info.size = len(result.value)

    return result


def _build_file_context(file_info: FileInfo) -> TemplateContext:
    """Build file context with file metadata.

    Args:
        file_info: FileInfo containing file metadata

    Returns:
        TemplateContext with file variables
    """
    file_vars = {
        "file": {
            "path": str(file_info.path),
            "basename": file_info.basename,
            "size": file_info.size,
            "mtime": file_info.mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "extension": file_info.path.suffix,
            "is_template": is_template_file(file_info),
        }
    }
    return TemplateContext(file_vars)


def _build_transient_context() -> TemplateContext:
    """Build transient context with current timestamp."""
    from mcp_guide.utils.template_context_cache import template_context_cache

    return template_context_cache.get_transient_context()


async def render_template_with_context_chain(
    content: str,
    category_name: Optional[str] = None,
    file_info: Optional[FileInfo] = None,
    file_path: str = "<template>",
) -> Result[str]:
    """Render template content with automatically built context chain.

    Args:
        content: Template content to render
        category_name: Optional category name for category-specific context
        file_info: Optional FileInfo for file-specific context
        file_path: File path for error reporting (used when file_info not provided)

    Returns:
        Result with rendered content or error
    """
    try:
        # Build base context chain (system → agent → project → category)
        base_context = await get_template_contexts(category_name)

        # Add file context if FileInfo provided
        if file_info is not None:
            file_context = _build_file_context(file_info)
            base_context = file_context.new_child(base_context)
            # Use file path from FileInfo for error reporting
            file_path = str(file_info.path)

        # Add transient context (timestamps, render time)
        transient_context = _build_transient_context()
        full_context = transient_context.new_child(base_context)

        # Render using the core renderer
        return render_template_content(content, full_context, file_path)

    except Exception as e:
        return Result.failure(
            error=f"Context chain building failed for {file_path}: {str(e)}",
            error_type="context_error",
            exception=e,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )
