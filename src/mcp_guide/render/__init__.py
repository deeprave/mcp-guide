"""Template rendering package."""

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
from mcp_guide.render.template import render_template

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
