"""Content models for template rendering."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.render.document_properties import DocumentContribution, DocumentProperties
from mcp_guide.render.frontmatter import Content, resolve_instruction
from mcp_guide.result_constants import AGENT_INSTRUCTION

logger = get_logger(__name__)

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
        partial_contributions: Rendered partial content and properties
        errors: Application-level errors signaled via {{#_error}} lambda
    """

    template_path: Path
    template_name: str
    partial_contributions: list[DocumentContribution] = field(default_factory=list)
    properties: DocumentProperties | None = None
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Derive parent properties using the existing template defaults."""
        if self.properties is None:
            default_cache = (
                CachePolicy.long_public() if str(self.template_path).endswith(".md") else CachePolicy.no_cache()
            )
            self.properties = DocumentProperties.from_frontmatter(
                self.frontmatter,
                cache_default=default_cache,
                disposition_default=AGENT_INSTRUCTION,
            )
        if self.properties.cache_diagnostic:
            logger.warning("%s in %s", self.properties.cache_diagnostic, self.template_path)

    @property
    def document_properties(self) -> DocumentProperties:
        """Resolve properties from this document and partials that rendered."""
        assert self.properties is not None
        return DocumentProperties.combine(
            (self.properties, *(contribution.properties for contribution in self.partial_contributions))
        )

    @property
    def template_type(self) -> str:
        """Get the parent template type for existing instruction resolution."""
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
        for contribution in self.partial_contributions:
            partial_fm = contribution.frontmatter
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

    @property
    def cache_policy(self) -> CachePolicy:
        """Resolve the restrictive cache policy for this rendered document."""
        return self.document_properties.cache_policy

    @property
    def disposition(self) -> str | None:
        """Resolve delivery disposition from this document and rendered partials."""
        return self.document_properties.disposition

    def log_discarded_errors(self, source: str) -> None:
        """Log and acknowledge any template errors that won't be surfaced to the client."""
        if self.errors:
            logger.warning("%s: template signaled errors that will be discarded: %s", source, self.errors)
