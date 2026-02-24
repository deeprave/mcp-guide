"""Content models for template rendering."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from mcp_guide.render.frontmatter import Content, resolve_instruction
from mcp_guide.result_constants import AGENT_INSTRUCTION

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
        partial_frontmatter: List of frontmatter from included partials
    """

    template_path: Path
    template_name: str
    partial_frontmatter: list[dict[str, Any]] = field(default_factory=list)

    @property
    def template_type(self) -> str:
        """Get template type from frontmatter or default to agent/instruction."""
        return self.frontmatter.get_str(FM_TYPE) or AGENT_INSTRUCTION

    @property
    def instruction(self) -> Optional[str]:
        """Get combined instruction from parent and partial frontmatter."""
        # Imports at function level to avoid circular import with frontmatter module
        from mcp_guide.content.utils import combine_instructions
        from mcp_guide.render.frontmatter import Frontmatter, get_frontmatter_type

        # Collect instructions from parent and all partials
        instructions_with_importance: list[tuple[str, bool]] = []

        # Add parent instruction
        parent_instruction, is_important = resolve_instruction(self.frontmatter, self.template_type)
        if parent_instruction:
            instructions_with_importance.append((parent_instruction, is_important))

        # Add partial instructions
        for partial_fm in self.partial_frontmatter:
            # Skip partials without explicit instruction or type to avoid injecting defaults
            if "instruction" not in partial_fm and "type" not in partial_fm:
                continue

            partial_frontmatter = Frontmatter(partial_fm)
            partial_type = get_frontmatter_type(partial_frontmatter)
            partial_instruction, partial_is_important = resolve_instruction(partial_frontmatter, partial_type)
            if partial_instruction:
                instructions_with_importance.append((partial_instruction, partial_is_important))

        return combine_instructions(instructions_with_importance)

    @property
    def description(self) -> Optional[str]:
        """Get description from frontmatter."""
        return self.frontmatter.get_str(FM_DESCRIPTION)

    @property
    def usage(self) -> Optional[str]:
        """Get usage string from frontmatter."""
        return self.frontmatter.get_str(FM_USAGE)

    @property
    def category(self) -> Optional[str]:
        """Get category from frontmatter."""
        return self.frontmatter.get_str(FM_CATEGORY)

    @property
    def aliases(self) -> Optional[list[str]]:
        """Get command aliases from frontmatter."""
        return self.frontmatter.get_list(FM_ALIASES)
