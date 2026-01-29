"""Content models for template rendering."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mcp_guide.result_constants import AGENT_INSTRUCTION
from mcp_guide.utils.frontmatter import Content, get_type_based_default_instruction

FM_INSTRUCTION = "instruction"
FM_TYPE = "type"
FM_DESCRIPTION = "description"
FM_REQUIRES_PREFIX = "requires-"
FM_CATEGORY = "category"
FM_USAGE = "usage"
FM_ALIASES = "aliases"
FM_INCLUDES = "includes"


@dataclass
class RenderedContent(Content):
    """Extends Content with template metadata.

    Attributes:
        template_path: Path to the template file
        template_name: Name of the template file
    """

    template_path: Path
    template_name: str

    @property
    def template_type(self) -> str:
        """Get template type from frontmatter or default to agent/instruction."""
        return self.frontmatter.get_str(FM_TYPE) or AGENT_INSTRUCTION

    @property
    def instruction(self) -> Optional[str]:
        """Get instruction from frontmatter or type-based default."""
        return self.frontmatter.get_str(FM_INSTRUCTION) or get_type_based_default_instruction(self.template_type)
