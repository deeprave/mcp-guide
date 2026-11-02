"""Template rendering utilities for Mustache templates."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, TypeVar

import chevron
from chevron import ChevronError

from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, ensure_within_limit
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS, FileInfo
from mcp_guide.render.bindings import build_template_bindings
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.document_properties import DocumentContribution, DocumentProperties
from mcp_guide.render.frontmatter import get_frontmatter_includes
from mcp_guide.render.partials import (
    PartialNotFoundError,
    UnsafePartialPathError,
    declared_partial_path,
    load_partial_content,
)
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_TEMPLATE, INSTRUCTION_VALIDATION_ERROR

if TYPE_CHECKING:
    from mcp_guide.render.recommendations import Recommendation

logger = get_logger(__name__)

_VT = TypeVar("_VT")


@dataclass
class TemplateRenderResult:
    """Rendered template output before document-level footnotes are appended."""

    content: str
    partial_contributions: list[DocumentContribution]
    errors: list[str]


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


async def render_template_content(
    content: str,
    context: TemplateContext,
    file_path: str = "<template>",
    transient_fn: Optional[Callable[[TemplateContext], TemplateContext]] = None,
    partials: Optional[Dict[str, str]] = None,
    pre_rendered_partial_contributions: Optional[Dict[str, list[DocumentContribution]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    requirements_context: Optional[Dict[str, Any]] = None,
    base_dir: Optional[Path] = None,
    resolver: Callable[[str | Path], Path] | None = None,
    recommendation_footnotes: Callable[[list["Recommendation"]], Awaitable[str]] | None = None,
    frontmatter_errors: list[str] | None = None,
    max_content_limit: int = DEFAULT_MAX_CONTENT_LIMIT,
) -> Result[TemplateRenderResult]:
    """Render template content with context.

    Args:
        content: Template content to render
        context: Template context data
        file_path: File path for error reporting
        transient_fn: Optional function to add transient data to context
        partials: Optional dictionary of partial templates
        pre_rendered_partial_contributions: Rendered policy partial contributors
        metadata: Optional frontmatter metadata to merge into context
        resolver: Server-side document-root resolver for filesystem partials

    Returns:
        Result with rendered content, rendered partial contributors, and errors
    """
    try:
        # Process metadata (frontmatter) if provided
        render_context = context
        processed_partials: Dict[str, str] = partials or {}
        partial_contributions_by_name: Dict[str, list[DocumentContribution]] = {
            name: list(contributions) for name, contributions in (pre_rendered_partial_contributions or {}).items()
        }
        errors = list(frontmatter_errors or [])

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
                        full_include_path = declared_partial_path(include_path)
                        partial_name = full_include_path.name.removeprefix("_")

                        # Load partial content using base directory
                        try:
                            # Build context for frontmatter requirements checking
                            context_dict = {**dict(render_context), **(requirements_context or {})}

                            if base_dir and resolver:
                                partial_content, partial_frontmatter, partial_errors = await load_partial_content(
                                    full_include_path,
                                    base_dir,
                                    context_dict,
                                    resolver=resolver,
                                    max_content_limit=max_content_limit,
                                )
                                errors.extend(f"Partial '{include_path}': {error}" for error in partial_errors)
                            else:
                                raise UnsafePartialPathError(
                                    "filesystem partial loading requires a document-root resolver"
                                )

                            processed_partials[partial_name] = partial_content
                            # Track frontmatter for partials that have content
                            if partial_frontmatter and partial_content:
                                properties = DocumentProperties.from_frontmatter(partial_frontmatter)
                                if properties.cache_diagnostic:
                                    logger.warning("%s in %s", properties.cache_diagnostic, full_include_path)
                                partial_contributions_by_name[partial_name] = [
                                    DocumentContribution(partial_content, partial_frontmatter, properties)
                                ]
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

        bindings = build_template_bindings(
            final_context,
            file_path,
            recommendations_enabled=recommendation_footnotes is not None,
        )

        # Use a tracking dict so we know which partials chevron actually renders
        tracking_partials: _TrackingDict[str] = _TrackingDict(processed_partials)

        # Render template with Chevron (TemplateContext works as ChainMap)
        logger.trace(f"Rendering template {file_path} with partials: {list(processed_partials.keys())}")
        rendered = await chevron.async_render(
            content,
            bindings.context,
            partials_path=None,
            partials_dict=tracking_partials,
            lambdas=bindings.lambdas,
            logger=logger,
        )
        if recommendation_footnotes:
            rendered += await recommendation_footnotes(bindings.functions.recommendations)
        ensure_within_limit(len(rendered.encode("utf-8")), limit_name="max-content-limit", limit=max_content_limit)
        logger.trace(f"Template {file_path} rendered content ({len(rendered)} chars): {rendered[:1024]}")

        # Only collect frontmatter from partials that were actually rendered
        partial_contributions: list[DocumentContribution] = []
        for name in tracking_partials.accessed:
            contributions = partial_contributions_by_name.get(name)
            if contributions is not None:
                partial_contributions.extend(contributions)
            elif name in processed_partials:
                partial_contributions.append(
                    DocumentContribution(processed_partials[name], {}, DocumentProperties.from_frontmatter(None))
                )

        return Result.ok(TemplateRenderResult(rendered, partial_contributions, [*errors, *bindings.functions.errors]))

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
