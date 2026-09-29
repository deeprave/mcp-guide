"""Template rendering package."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp_guide.render.template import render_template

from mcp_guide.render.content import (
    FM_ALIASES,
    FM_CATEGORY,
    FM_DESCRIPTION,
    FM_INCLUDES,
    FM_INSTRUCTION,
    FM_REQUIRES_PREFIX,
    FM_TYPE,
    FM_USAGE,
    RenderedContent,
)

__all__ = [
    "FM_ALIASES",
    "FM_CATEGORY",
    "FM_DESCRIPTION",
    "FM_INCLUDES",
    "FM_INSTRUCTION",
    "FM_REQUIRES_PREFIX",
    "FM_TYPE",
    "FM_USAGE",
    "RenderedContent",
    "render_template",
]


def __getattr__(name: str) -> Any:
    """Load the template renderer lazily to avoid the renderer/discovery import cycle."""
    if name == "render_template":
        from mcp_guide.render.template import render_template

        return render_template
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
