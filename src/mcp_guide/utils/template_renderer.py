"""Template rendering utilities for Mustache templates."""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import chevron
from chevron import ChevronError

from mcp_core.result import Result
from mcp_guide.tools.tool_constants import INSTRUCTION_FILE_ERROR, INSTRUCTION_VALIDATION_ERROR
from mcp_guide.utils.file_discovery import TEMPLATE_EXTENSIONS, FileInfo
from mcp_guide.utils.frontmatter import get_frontmatter_includes
from mcp_guide.utils.template_context import TemplateContext
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.utils.template_functions import TemplateFunctions
from mcp_guide.utils.template_partials import load_partial_content, resolve_partial_paths


def is_template_file(file_info: FileInfo) -> bool:
    """Check if FileInfo represents a template file.

    Args:
        file_info: FileInfo to check

    Returns:
        True if file has template extension
    """
    return str(file_info.path).endswith(TEMPLATE_EXTENSIONS)


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
    partials: Optional[Dict[str, str]] = None,
) -> Result[str]:
    """Render template content with context.

    Args:
        content: Template content to render
        context: Template context data
        file_path: File path for error reporting
        transient_fn: Optional function to add transient data to context
        partials: Optional dictionary of partial templates

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
                "pad_right": _safe_lambda(functions.pad_right),
            }
        )

        # Render template with Chevron (TemplateContext works as ChainMap)
        rendered = chevron.render(content, template_context, partials_dict=partials or {})  # type: ignore[arg-type]
        return Result.ok(rendered)

    except ChevronError as e:
        # Enhanced Chevron-specific error handling with line context
        error_msg = str(e)
        line_context = _extract_line_context(content, error_msg)
        full_error = f"Template syntax error in {file_path}: {error_msg}\n{line_context}"

        logging.error(full_error)
        return Result.failure(
            error=full_error,
            error_type="template_error",
            exception=e,
            instruction=f"Fix template syntax in {file_path}. Check for unclosed sections, mismatched tags, or invalid mustache syntax.",
        )
    except Exception as e:
        # General error handling for other exceptions
        logging.warning(f"Template rendering error in {file_path}: {str(e)}")
        return Result.failure(
            error=f"Template rendering failed for {file_path}: {str(e)}",
            error_type="template_error",
            exception=e,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )


def _extract_line_context(content: str, error_msg: str) -> str:
    """Extract line context from template content based on error message."""
    import re

    # Try to extract line number from error message
    line_match = re.search(r"line (\d+)", error_msg, re.IGNORECASE)
    if not line_match:
        return ""

    line_num = int(line_match.group(1))
    lines = content.split("\n")

    if line_num < 1 or line_num > len(lines):
        return ""

    # Show context: 2 lines before, error line, 2 lines after
    start = max(0, line_num - 3)
    end = min(len(lines), line_num + 2)

    context_lines = []
    for i in range(start, end):
        prefix = ">>> " if i == line_num - 1 else "    "
        context_lines.append(f"{prefix}{i + 1:4d} | {lines[i]}")

    return "\n" + "\n".join(context_lines)


def render_file_content(
    file_info: FileInfo,
    context: TemplateContext | None = None,
    base_dir: Path | None = None,
    _include_chain: set[Path] | None = None,
) -> Result[str]:
    """Render file content, applying template rendering if needed.

    Args:
        file_info: FileInfo with content to render
        context: Template context (if None, pass through content unchanged)
        base_dir: Base directory for resolving partial paths
        _include_chain: Internal parameter to track circular includes

    Returns:
        Result with rendered content or original content
    """
    # Initialize include chain tracking
    if _include_chain is None:
        _include_chain = set()

    # Check for circular includes
    current_path = base_dir / file_info.path if base_dir else file_info.path
    if current_path in _include_chain:
        return Result.failure(
            error=f"Circular include detected: {current_path}",
            error_type="circular_include",
            instruction="Remove circular dependencies in template includes",
        )

    _include_chain.add(current_path)

    if file_info.content is None:
        return Result.failure(
            error=f"File content not loaded: {file_info.path}",
            error_type="content_error",
            instruction=INSTRUCTION_FILE_ERROR,
        )

    # Pass through non-template files unchanged
    if not is_template_file(file_info) or context is None:
        return Result.ok(file_info.content)

    # Process includes from frontmatter
    partials = {}
    if file_info.frontmatter:
        includes = get_frontmatter_includes(file_info.frontmatter)
        if includes:
            try:
                # Determine template directory for partial resolution
                if base_dir:
                    # Use base_dir to resolve the actual template location
                    template_path = base_dir / file_info.path
                else:
                    # Fallback to file_info path
                    template_path = file_info.path

                # Resolve partial paths relative to template directory
                partial_paths = resolve_partial_paths(template_path, includes)

                # Load partial content
                for i, partial_path in enumerate(partial_paths):
                    # Extract partial name from include path
                    include_path = includes[i]
                    partial_name = Path(include_path).stem
                    # Remove leading underscore if present (partial naming convention)
                    if partial_name.startswith("_"):
                        partial_name = partial_name[1:]
                    partials[partial_name] = load_partial_content(partial_path)

            except Exception as e:
                return Result.failure(
                    error=f"Failed to load partials for {file_info.path}: {str(e)}",
                    error_type="partial_error",
                    instruction=f"Check that partial files exist and are readable: {includes}",
                )

    # Render template files with partials
    result = render_template_content(file_info.content, context, str(file_info.path), partials=partials)

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
            "name": file_info.name,
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
