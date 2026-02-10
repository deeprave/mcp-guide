"""Template rendering utilities for Mustache templates."""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

import chevron
from chevron import ChevronError

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS, FileInfo
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import get_frontmatter_includes, resolve_instruction
from mcp_guide.render.functions import TemplateFunctions
from mcp_guide.render.partials import PartialNotFoundError, load_partial_content
from mcp_guide.result import Result
from mcp_guide.result_constants import INSTRUCTION_VALIDATION_ERROR

logger = get_logger(__name__)


def get_partial_name(include_path: str | Path) -> str:
    """Extract partial name from include path.

    Args:
        include_path: Path to the partial file

    Returns:
        Partial name with leading underscore removed if present
    """
    path = Path(include_path)
    stem = path.stem
    return stem[1:] if stem.startswith("_") else stem


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
            logger.exception("Error while evaluating template lambda", exc_info=True)
            # Return a user-friendly error string with exception type preserved
            return f"[Template Error ({type(e).__name__}): {e}]"

    return wrapper


async def render_template_content(
    content: str,
    context: TemplateContext,
    file_path: str = "<template>",
    transient_fn: Optional[Callable[[TemplateContext], TemplateContext]] = None,
    partials: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    base_dir: Optional[Path] = None,
) -> Result[str]:
    """Render template content with context.

    Args:
        content: Template content to render
        context: Template context data
        file_path: File path for error reporting
        transient_fn: Optional function to add transient data to context
        partials: Optional dictionary of partial templates
        metadata: Optional frontmatter metadata to merge into context

    Returns:
        Result with rendered content or error
    """
    try:
        # Process metadata (frontmatter) if provided
        render_context = context
        processed_partials = partials or {}

        if metadata:
            # Add frontmatter data to context
            metadata_context = TemplateContext(metadata)
            render_context = metadata_context.new_child(context)

            # Extract partials from frontmatter includes
            if includes := get_frontmatter_includes(metadata):
                logger.trace(f"Processing includes for template {file_path}: {includes}")
                try:
                    # Process includes and merge with existing partials
                    for include_path in includes:
                        partial_name = Path(include_path).stem
                        if partial_name.startswith("_"):
                            partial_name = partial_name[1:]

                        # Construct proper partial path with _ prefix
                        include_dir = Path(include_path).parent
                        partial_filename = f"_{partial_name}"
                        full_include_path = include_dir / partial_filename

                        # Load partial content using base directory
                        try:
                            # Build context for frontmatter requirements checking
                            context_dict = dict(render_context) if render_context else {}

                            if base_dir:
                                partial_content, partial_frontmatter = await load_partial_content(
                                    full_include_path, base_dir, context_dict
                                )
                            else:
                                # Fallback to file path parent if no base_dir provided
                                file_parent = Path(file_path).parent if file_path != "<template>" else Path.cwd()
                                partial_content, partial_frontmatter = await load_partial_content(
                                    full_include_path, file_parent, context_dict
                                )

                            # Merge partial frontmatter instruction with parent frontmatter
                            # Resolve instructions from both parent and partial
                            parent_instruction, parent_is_important = resolve_instruction(metadata)
                            partial_instruction, partial_is_important = resolve_instruction(partial_frontmatter)

                            # If partial has important instruction, override parent's instruction in metadata
                            if partial_is_important and partial_instruction:
                                metadata["instruction"] = f"! {partial_instruction}"
                                logger.trace(
                                    f"Partial '{partial_name}' overriding parent instruction with: {partial_instruction}"
                                )

                            processed_partials[partial_name] = partial_content
                            logger.trace(f"Loaded partial '{partial_name}' from {include_path}")
                        except PartialNotFoundError as e:
                            logger.error(f"Partial template not found: {include_path} - {e}")
                        except (OSError, PermissionError) as e:
                            logger.error(f"Failed to read partial file {include_path}: {e}")
                        except ValueError as e:
                            logger.error(f"Invalid partial path {include_path}: {e}")

                except Exception as e:
                    logger.error(f"Error processing includes for {file_path}: {e}")

        # Apply transient function if provided
        final_context = transient_fn(render_context) if transient_fn else render_context

        # Create template functions and inject into context with error handling
        functions = TemplateFunctions(final_context)
        template_context = final_context.new_child(
            {
                "format_date": _safe_lambda(functions.format_date),
                "truncate": _safe_lambda(functions.truncate),
                "highlight_code": _safe_lambda(functions.highlight_code),
                "pad_right": _safe_lambda(functions.pad_right),
            }
        )

        # Render template with Chevron (TemplateContext works as ChainMap)
        logger.trace(f"Rendering template {file_path} with partials: {list(processed_partials.keys())}")
        rendered = chevron.render(content, template_context, partials_dict=processed_partials)  # type: ignore[arg-type]
        logger.trace(f"Template {file_path} rendered content ({len(rendered)} chars): {rendered[:1024]}")
        return Result.ok(rendered)

    except ChevronError as e:
        # Enhanced Chevron-specific error handling with line context
        error_msg = str(e)
        line_context = _extract_line_context(content, error_msg)
        full_error = f"Template syntax error in {file_path}: {error_msg}\n{line_context}"

        logger.error(full_error)
        return Result.failure(
            error=full_error,
            error_type="template_error",
            exception=e,
            instruction=f"Fix template syntax in {file_path}. Check for unclosed sections, mismatched tags, or invalid mustache syntax.",
        )
    except Exception as e:
        # General error handling for other exceptions
        logger.warning(f"Template rendering error in {file_path}: {str(e)}")
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
    from mcp_guide.render.cache import template_context_cache

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
        return await render_template_content(content, full_context, file_path)

    except Exception as e:
        return Result.failure(
            error=f"Context chain building failed for {file_path}: {str(e)}",
            error_type="context_error",
            exception=e,
            instruction=INSTRUCTION_VALIDATION_ERROR,
        )
