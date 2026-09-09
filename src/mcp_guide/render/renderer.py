"""Template rendering utilities for Mustache templates."""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

import chevron
from chevron import ChevronError

from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, ensure_within_limit
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import get_prompt_name
from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS, FileInfo
from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import get_frontmatter_includes
from mcp_guide.render.functions import TemplateFunctions
from mcp_guide.render.partials import PartialNotFoundError, UnsafePartialPathError, load_partial_content
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_TEMPLATE, INSTRUCTION_VALIDATION_ERROR

logger = get_logger(__name__)

_VT = TypeVar("_VT")


class _TrackingDict(Dict[str, _VT]):
    """Dict subclass that records which keys were accessed (for chevron partial tracking)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.accessed: dict[str, None] = {}

    def __getitem__(self, key: str) -> _VT:
        self.accessed[key] = None
        return super().__getitem__(key)

    def get(self, key: object, default: Any = None) -> Any:
        if isinstance(key, str):
            self.accessed[key] = None
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            self.accessed[key] = None
        return super().__contains__(key)


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
    pre_rendered_partial_frontmatter: Optional[Dict[str, list[Dict[str, Any]]]] = None,
    pre_rendered_partial_cache_policies: Optional[Dict[str, list[CachePolicy]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    base_dir: Optional[Path] = None,
    resolver: Callable[[str | Path], Path] | None = None,
    max_content_limit: int = DEFAULT_MAX_CONTENT_LIMIT,
) -> Result[tuple[str, list[Dict[str, Any]], list[CachePolicy], list[str]]]:
    """Render template content with context.

    Args:
        content: Template content to render
        context: Template context data
        file_path: File path for error reporting
        transient_fn: Optional function to add transient data to context
        partials: Optional dictionary of partial templates
        pre_rendered_partial_frontmatter: Frontmatter for pre-rendered partial contributors
        pre_rendered_partial_cache_policies: Resolved policies for pre-rendered partial contributors
        metadata: Optional frontmatter metadata to merge into context
        resolver: Server-side document-root resolver for filesystem partials

    Returns:
        Result with rendered content, partial frontmatter, cache policies, and errors
    """
    try:
        # Process metadata (frontmatter) if provided
        render_context = context
        processed_partials: Dict[str, str] = partials or {}
        partial_frontmatter_list: list[Dict[str, Any]] = []
        # Maps partial name → frontmatter contributors for rendered partial content.
        partial_frontmatter_by_name: Dict[str, list[Dict[str, Any]]] = {
            name: list(frontmatter) for name, frontmatter in (pre_rendered_partial_frontmatter or {}).items()
        }
        partial_cache_policies_by_name: Dict[str, list[CachePolicy]] = {
            name: list(policies) for name, policies in (pre_rendered_partial_cache_policies or {}).items()
        }

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

                            if base_dir and resolver:
                                partial_content, partial_frontmatter = await load_partial_content(
                                    full_include_path,
                                    base_dir,
                                    context_dict,
                                    resolver=resolver,
                                    max_content_limit=max_content_limit,
                                )
                            else:
                                raise UnsafePartialPathError(
                                    "filesystem partial loading requires a document-root resolver"
                                )

                            processed_partials[partial_name] = partial_content
                            # Track frontmatter for partials that have content
                            if partial_frontmatter and partial_content:
                                partial_frontmatter_by_name[partial_name] = [partial_frontmatter]
                                policy, diagnostic = CachePolicy.parse_with_diagnostic(partial_frontmatter.get("cache"))
                                if diagnostic:
                                    logger.warning("%s in %s", diagnostic, full_include_path)
                                partial_cache_policies_by_name[partial_name] = [policy]
                            logger.trace(f"Loaded partial '{partial_name}' from {include_path}")
                        except PartialNotFoundError as e:
                            logger.error(f"Partial template not found: {include_path} - {e}")
                        except (OSError, PermissionError) as e:
                            logger.error(f"Failed to read partial file {include_path}: {e}")
                        except UnsafePartialPathError as e:
                            logger.warning("Unsafe partial reference omitted: %s", e)
                        except ValueError as e:
                            logger.error(f"Invalid partial path {include_path}: {e}")

                except Exception as e:
                    logger.error(f"Error processing includes for {file_path}: {e}")

        # Apply transient function if provided
        final_context = transient_fn(render_context) if transient_fn else render_context

        # Create template functions and inject into context with error handling
        functions = TemplateFunctions(final_context)
        workflow_context = final_context.get("workflow")
        workflow_vars = {}
        if isinstance(workflow_context, dict):
            workflow_vars = {
                "workflow": {
                    **workflow_context,
                    "contains": _safe_lambda(functions.workflow_contains),
                    "notcontains": _safe_lambda(functions.workflow_notcontains),
                }
            }
        stem = Path(file_path).stem if file_path else "template"
        template_context = final_context.new_child(
            {
                "template_name": stem.lstrip("_"),
                "prompt": get_prompt_name(),
                "_error": functions._error,
                "format_date": _safe_lambda(functions.format_date),
                "truncate": _safe_lambda(functions.truncate),
                "highlight_code": _safe_lambda(functions.highlight_code),
                "pad_right": _safe_lambda(functions.pad_right),
                "contains": _safe_lambda(functions.contains),
                "equals": _safe_lambda(functions.equals),
                "notequals": _safe_lambda(functions.notequals),
                "time_ago": _safe_lambda(functions.time_ago),
                "resource": _safe_lambda(functions.resource),
                "command": _safe_lambda(functions.command),
                "command-args": _safe_lambda(functions.command_args),
                "command-flags": _safe_lambda(functions.command_flags),
                "command-alias": _safe_lambda(functions.command_alias),
                **workflow_vars,
            }
        )

        # Use a tracking dict so we know which partials chevron actually renders
        tracking_partials: _TrackingDict[str] = _TrackingDict(processed_partials)

        # Render template with Chevron (TemplateContext works as ChainMap)
        logger.trace(f"Rendering template {file_path} with partials: {list(processed_partials.keys())}")
        rendered = chevron.render(content, template_context, partials_dict=tracking_partials)
        ensure_within_limit(len(rendered.encode("utf-8")), limit_name="max-content-limit", limit=max_content_limit)
        logger.trace(f"Template {file_path} rendered content ({len(rendered)} chars): {rendered[:1024]}")

        # Only collect frontmatter from partials that were actually rendered
        partial_frontmatter_list = [
            frontmatter
            for name in tracking_partials.accessed
            for frontmatter in partial_frontmatter_by_name.get(name, [])
        ]
        partial_cache_policies = [
            policy
            for name in tracking_partials.accessed
            for policy in partial_cache_policies_by_name.get(name) or [CachePolicy.no_cache()]
        ]

        return Result.ok((rendered, partial_frontmatter_list, partial_cache_policies, functions.errors))

    except ChevronError as e:
        # Enhanced Chevron-specific error handling with line context
        error_msg = str(e)
        line_context = _extract_line_context(content, error_msg)
        full_error = f"Template syntax error in {file_path}: {error_msg}\n{line_context}"

        logger.error(full_error)
        return Result.failure(
            error=full_error,
            error_type=ERROR_TEMPLATE,
            exception=e,
            instruction=f"Fix template syntax in {file_path}. Check for unclosed sections, mismatched tags, or invalid mustache syntax.",
        )
    except Exception as e:
        # General error handling for other exceptions
        logger.warning(f"Template rendering error in {file_path}: {str(e)}")
        return Result.failure(
            error=f"Template rendering failed for {file_path}: {str(e)}",
            error_type=ERROR_TEMPLATE,
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
