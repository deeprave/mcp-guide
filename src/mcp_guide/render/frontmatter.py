"""Front-matter parsing utilities for YAML metadata extraction."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import aiofiles
import yaml

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render.frontmatter_types import Frontmatter
from mcp_guide.render.requires import check_requires_directive
from mcp_guide.result_constants import (
    AGENT_INFO,
    AGENT_INSTRUCTION,
    AGENT_REQUIREMENTS,
    INSTRUCTION_AGENT_INFO,
    INSTRUCTION_AGENT_INSTRUCTIONS,
    INSTRUCTION_AGENT_REQUIREMENTS,
    INSTRUCTION_DISPLAY_ONLY,
    USER_INFO,
)

if TYPE_CHECKING:
    from mcp_guide.render.context import TemplateContext

__all__ = [
    "Frontmatter",
    "Content",
    "ProcessedFrontmatter",
    "resolve_instruction",
    "parse_content_with_frontmatter",
    "check_frontmatter_requirements",
    "process_frontmatter",
    "process_file",
]

logger = get_logger(__name__)

# Pre-compile regex for important instruction prefix
IMPORTANT_PREFIX_PATTERN = re.compile(r"^\^\s*")


def check_frontmatter_requirements(frontmatter: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Check if frontmatter requirements are satisfied by context.

    Args:
        frontmatter: Parsed frontmatter dictionary
        context: Context dictionary (e.g., project flags, workflow state)

    Returns:
        True if requirements are satisfied, False if content should be suppressed
    """
    for key, required_value in frontmatter.items():
        if not key.startswith("requires-"):
            continue

        flag_name = key[9:]  # Remove "requires-" prefix
        actual_value = context.get(flag_name)

        if not check_requires_directive(required_value, actual_value):
            return False

    return True


@dataclass
class Content:
    """Represents parsed content with frontmatter."""

    frontmatter: Frontmatter
    frontmatter_length: int
    content: str
    content_length: int


@dataclass
class ProcessedFrontmatter:
    """Result of frontmatter processing with requirements check and field rendering."""

    frontmatter: Frontmatter
    content: str
    frontmatter_length: int
    content_length: int


def parse_content_with_frontmatter(content: str) -> Content:
    """Parse content string and extract frontmatter.

    Args:
        content: Raw content string

    Returns:
        Content object with parsed frontmatter and clean content
    """
    if not content.startswith("---\n"):
        return Content(frontmatter=Frontmatter(), frontmatter_length=0, content=content, content_length=len(content))

    # Find the closing ---
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return Content(frontmatter=Frontmatter(), frontmatter_length=0, content=content, content_length=len(content))

    # Extract and parse YAML
    yaml_content = "\n".join(lines[1:end_idx])
    clean_content = "\n".join(lines[end_idx + 1 :])
    frontmatter_length = len("\n".join(lines[: end_idx + 1])) + 1  # +1 for final newline

    try:
        metadata = yaml.safe_load(yaml_content)
        # Lowercase all keys for case-insensitive access
        if isinstance(metadata, dict):
            metadata = Frontmatter({k.lower(): v for k, v in metadata.items()})
        else:
            metadata = Frontmatter()
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in frontmatter: {e}")
        metadata = Frontmatter()

    return Content(
        frontmatter=metadata,
        frontmatter_length=frontmatter_length,
        content=clean_content,
        content_length=len(clean_content),
    )


async def read_content_with_frontmatter(file_path: Path) -> Content:
    """Read file and parse frontmatter.

    Args:
        file_path: Path to file to read

    Returns:
        Content object with parsed frontmatter and clean content
    """
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            raw_content = await f.read()
        return parse_content_with_frontmatter(raw_content)
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Could not read file {file_path}: {e}")
        return Content(frontmatter=Frontmatter(), frontmatter_length=0, content="", content_length=0)


def get_frontmatter_instruction(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract instruction field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Instruction string or None if not found
    """
    from mcp_guide.render.content import FM_INSTRUCTION

    if not frontmatter:
        return None
    instruction = frontmatter.get(FM_INSTRUCTION)
    return instruction if isinstance(instruction, str) else None


def get_frontmatter_type(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract type field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Type string or None if not found
    """
    if not frontmatter:
        return None
    type_value = frontmatter.get("type")
    return type_value if isinstance(type_value, str) else None


def get_frontmatter_description(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract description field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Description string or None if not found
    """
    if not frontmatter:
        return None
    description = frontmatter.get("description")
    return description if isinstance(description, str) else None


def get_frontmatter_includes(frontmatter: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    """Extract includes field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Includes list or None if not found
    """
    if not frontmatter:
        return None
    includes = frontmatter.get("includes")
    return includes if isinstance(includes, list) and all(isinstance(x, str) for x in includes) else None


def get_type_based_default_instruction(content_type: Optional[str]) -> str:
    """Get default instruction based on content type.

    Args:
        content_type: Content type from frontmatter

    Returns:
        Default instruction string
    """
    return get_default_instruction_for_type(content_type)


def resolve_instruction(
    frontmatter: Optional[Dict[str, Any]], content_type: Optional[str] = None
) -> tuple[Optional[str], bool]:
    """Resolve instruction from frontmatter with support for important override.

    Args:
        frontmatter: Parsed frontmatter dictionary
        content_type: Content type for fallback default instruction

    Returns:
        Tuple of (instruction, is_important) where:
        - instruction: Resolved instruction string or None
        - is_important: True if instruction has ^ prefix (overrides regular instructions)
    """
    from mcp_guide.render.content import FM_INSTRUCTION

    # Get explicit instruction from frontmatter
    if frontmatter:
        instruction = frontmatter.get(FM_INSTRUCTION)
        if isinstance(instruction, str) and instruction.strip():
            # Check for important prefix
            if IMPORTANT_PREFIX_PATTERN.match(instruction):
                clean_instruction = IMPORTANT_PREFIX_PATTERN.sub("", instruction).strip()
                return (clean_instruction if clean_instruction else None, True)
            return (instruction, False)

    # Fallback to type-based default
    default_instruction = get_type_based_default_instruction(content_type)
    return (default_instruction, False)


async def get_frontmatter_description_from_file(file_path: Path) -> Optional[str]:
    """Extract description from file's frontmatter.

    Args:
        file_path: Path to file to read

    Returns:
        Description string or None if not found
    """
    content = await read_content_with_frontmatter(file_path)
    if not content.frontmatter:
        return None
    description = content.frontmatter.get("description")
    return description if isinstance(description, str) else None


def validate_content_type(content_type: Optional[str]) -> bool:
    """Validate if content type is one of the supported types.

    Args:
        content_type: Content type string to validate

    Returns:
        True if valid, False otherwise
    """
    if not content_type:
        return False

    valid_types = {USER_INFO, AGENT_INFO, AGENT_INSTRUCTION, AGENT_REQUIREMENTS}
    return content_type in valid_types


def get_default_instruction_for_type(content_type: Optional[str]) -> str:
    """Get default instruction based on content type.

    Args:
        content_type: Content type from frontmatter

    Returns:
        Default instruction string or None for agent/instruction type
    """

    type_instructions = {
        USER_INFO: INSTRUCTION_DISPLAY_ONLY,
        AGENT_INFO: INSTRUCTION_AGENT_INFO,
        AGENT_INSTRUCTION: INSTRUCTION_AGENT_INSTRUCTIONS,
        AGENT_REQUIREMENTS: INSTRUCTION_AGENT_REQUIREMENTS,
    }

    return type_instructions.get(content_type or "", INSTRUCTION_DISPLAY_ONLY)


async def process_frontmatter(
    content: str,
    requirements_context: Optional[Dict[str, Any]],
    render_context: Optional["TemplateContext"] = None,
) -> Optional[ProcessedFrontmatter]:
    """Process frontmatter: parse, check requirements, render fields.

    Args:
        content: Raw content with frontmatter
        requirements_context: Context for requires-* checking. If None, requirements are not checked.
        render_context: Optional context for rendering instruction/description

    Returns:
        ProcessedFrontmatter if requirements met, None if filtered

    Note:
        Requirements checking is skipped when requirements_context is None.
        Empty dict is treated as "no requirements to check" (all pass).
        Missing flags in requirements_context are treated as False (requirement not met).
    """
    # Parse frontmatter
    parsed = parse_content_with_frontmatter(content)

    # Check requirements only if context provided and not empty
    if requirements_context is not None and not check_frontmatter_requirements(
        parsed.frontmatter, requirements_context
    ):
        return None

    # Render instruction and description fields if render_context provided
    if render_context:
        import chevron

        context_dict = dict(render_context)
        for field in ("instruction", "description"):
            if field in parsed.frontmatter and isinstance(parsed.frontmatter[field], str):
                try:
                    parsed.frontmatter[field] = chevron.render(parsed.frontmatter[field], context_dict)
                except chevron.ChevronError as e:
                    logger.warning(f"Failed to render {field} field: {e}")

    return ProcessedFrontmatter(
        frontmatter=parsed.frontmatter,
        content=parsed.content,
        frontmatter_length=parsed.frontmatter_length,
        content_length=parsed.content_length,
    )


async def process_file(
    file_info: Any,
    requirements_context: Optional[Dict[str, Any]],
    render_context: Optional["TemplateContext"],
) -> Optional[ProcessedFrontmatter]:
    """Process a non-template file: read, parse frontmatter, check requirements.

    Args:
        file_info: FileInfo object with file path
        requirements_context: Context for requires-* checking. If None, requirements are not checked.
        render_context: Optional context for rendering frontmatter fields

    Returns:
        ProcessedFrontmatter if requirements met, None if filtered

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
        UnicodeDecodeError: If file isn't valid UTF-8
    """
    async with aiofiles.open(file_info.path, "r", encoding="utf-8") as f:
        content = await f.read()

    return await process_frontmatter(content, requirements_context, render_context)
