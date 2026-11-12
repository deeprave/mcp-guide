"""Explicit Guide extension bindings for Mustache rendering."""

import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import chevron

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import get_prompt_name
from mcp_guide.core.tool_decorator import get_tool_prefix
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.functions import TemplateFunctions

logger = get_logger(__name__)


class FrontmatterExtensionError(ValueError):
    """Raised when an extension cannot be used in renderable frontmatter."""


@dataclass
class TemplateBindings:
    """Data context, stateful functions, and explicit extensions for one render."""

    context: TemplateContext
    functions: TemplateFunctions
    lambdas: dict[str, Callable[..., Any]]


def _safe_lambda(
    func: Callable[..., Any],
    protocol: Callable[[Callable[..., Any]], Callable[..., Any]],
    *,
    errors: list[str] | None = None,
) -> Callable[..., Any]:
    """Wrap an extension to convert implementation errors into safe template text."""

    async def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            result = func(*args, **kwargs)
            return await result if inspect.isawaitable(result) else result
        except Exception as error:
            logger.exception("Error while evaluating template lambda", exc_info=True)
            if errors is not None:
                errors.append(f"Template extension failed: {error}")
            return f"[Template Error ({type(error).__name__}): {error}]"

    return protocol(wrapper)


@chevron.func
def tool_prefix_display() -> str:
    """Return the configured tool prefix, or its status display fallback."""
    return get_tool_prefix() or "None"


@chevron.compat
async def _frontmatter_recommend(*_: Any, **__: Any) -> str:
    """Reject recommendations where Guide cannot emit their footnotes."""
    raise FrontmatterExtensionError(
        "`recommend` is not supported in renderable frontmatter because it requires an active delivery session"
    )


def _build_lambda_registry(
    functions: TemplateFunctions,
    *,
    frontmatter: bool,
) -> dict[str, Callable[..., Any]]:
    """Create extensions for a body render or the frontmatter profile."""
    errors = functions.errors if frontmatter else None

    def safe(
        func: Callable[..., Any],
        protocol: Callable[[Callable[..., Any]], Callable[..., Any]],
    ) -> Callable[..., Any]:
        return _safe_lambda(func, protocol, errors=errors)

    lambdas = {
        "_error": safe(functions._error, chevron.compat),
        "prompt": safe(get_prompt_name, chevron.func),
        "tool_prefix": safe(get_tool_prefix, chevron.func),
        "tool_prefix_display": tool_prefix_display,
        "documents-path": safe(functions.documents_path, chevron.func),
        "handoff-context-path": safe(functions.handoff_context_path, chevron.func),
        "recommend": _frontmatter_recommend if frontmatter else functions.recommend,
        "format_date": safe(functions.format_date, chevron.compat),
        "truncate": safe(functions.truncate, chevron.compat),
        "shell_quote": safe(functions.shell_quote, chevron.compat),
        "highlight_code": safe(functions.highlight_code, chevron.compat),
        "pad_right": safe(functions.pad_right, chevron.compat),
        "workflow.contains": safe(functions.workflow_contains, chevron.section),
        "workflow.notcontains": safe(functions.workflow_notcontains, chevron.section),
        "equals": safe(functions.equals, chevron.section),
        "notequals": safe(functions.notequals, chevron.section),
        "time_ago": safe(functions.time_ago, chevron.compat),
        "resource": safe(functions.resource, chevron.section),
        "command": safe(functions.command, chevron.section),
        "command-args": safe(functions.command_args, chevron.compat),
        "command-flags": safe(functions.command_flags, chevron.compat),
        "command-alias": safe(functions.command_alias, chevron.compat),
    }
    openspec = functions.context.get("openspec")
    if isinstance(openspec, Mapping):
        for name in ("request_changes", "refresh_changes"):
            callback = openspec.get(name)
            if callable(callback):
                lambdas[f"openspec.{name}"] = safe(callback, chevron.section)
    return lambdas


def build_template_lambda_registry(
    context: TemplateContext,
    *,
    recommendations_enabled: bool,
) -> tuple[TemplateFunctions, dict[str, Callable[..., Any]]]:
    """Create the stateful functions and data-separate extension registry for one render."""
    functions = TemplateFunctions(context, recommendations_enabled=recommendations_enabled)
    return functions, _build_lambda_registry(functions, frontmatter=False)


def build_frontmatter_lambda_registry(
    context: TemplateContext,
) -> tuple[TemplateFunctions, dict[str, Callable[..., Any]]]:
    """Create the frontmatter extension profile and its diagnostic state."""
    functions = TemplateFunctions(context, recommendations_enabled=False)
    return functions, _build_lambda_registry(functions, frontmatter=True)


def build_template_bindings(
    context: TemplateContext,
    file_path: str,
    *,
    recommendations_enabled: bool,
) -> TemplateBindings:
    """Create the data-only context and explicit extensions for a template body."""
    functions, lambdas = build_template_lambda_registry(
        context,
        recommendations_enabled=recommendations_enabled,
    )
    stem = Path(file_path).stem if file_path else "template"
    return TemplateBindings(
        context=context.new_child({"template_name": stem.lstrip("_")}),
        functions=functions,
        lambdas=lambdas,
    )
