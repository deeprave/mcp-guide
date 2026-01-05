"""Front-matter parsing utilities for YAML metadata extraction."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import yaml

from mcp_core.mcp_log import get_logger
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

logger = get_logger(__name__)


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

        # Get actual value from context
        actual_value = context.get(flag_name)

        # Handle different requirement types
        if isinstance(required_value, bool):
            # Simple boolean requirement
            if bool(actual_value) != required_value:
                return False
        elif isinstance(required_value, list):
            # Must match one of the values in list
            if actual_value not in required_value:
                return False
        else:
            # Exact match requirement
            if actual_value != required_value:
                return False

    return True


@dataclass
class Content:
    """Represents parsed content with frontmatter."""

    frontmatter: Dict[str, Any]
    frontmatter_length: int
    content: str
    content_length: int


def parse_content_with_frontmatter(content: str) -> Content:
    """Parse content string and extract frontmatter.

    Args:
        content: Raw content string

    Returns:
        Content object with parsed frontmatter and clean content
    """
    if not content.startswith("---\n"):
        return Content(frontmatter={}, frontmatter_length=0, content=content, content_length=len(content))

    # Find the closing ---
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return Content(frontmatter={}, frontmatter_length=0, content=content, content_length=len(content))

    # Extract and parse YAML
    yaml_content = "\n".join(lines[1:end_idx])
    clean_content = "\n".join(lines[end_idx + 1 :])
    frontmatter_length = len("\n".join(lines[: end_idx + 1])) + 1  # +1 for final newline

    try:
        metadata = yaml.safe_load(yaml_content)
        # Lowercase all keys for case-insensitive access
        if isinstance(metadata, dict):
            metadata = {k.lower(): v for k, v in metadata.items()}
        else:
            metadata = {}
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in frontmatter: {e}")
        metadata = {}

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
        return Content(frontmatter={}, frontmatter_length=0, content="", content_length=0)


def get_frontmatter_instruction(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract instruction field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Instruction string or None if not found
    """
    return frontmatter.get("instruction") if frontmatter else None


def get_frontmatter_type(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract type field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Type string or None if not found
    """
    return frontmatter.get("type") if frontmatter else None


def get_frontmatter_description(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract description field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Description string or None if not found
    """
    return frontmatter.get("description") if frontmatter else None


def get_frontmatter_includes(frontmatter: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    """Extract includes field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Includes list or None if not found
    """
    return frontmatter.get("includes") if frontmatter else None


def get_type_based_default_instruction(content_type: Optional[str]) -> str:
    """Get default instruction based on content type.

    Args:
        content_type: Content type from frontmatter

    Returns:
        Default instruction string
    """
    return get_default_instruction_for_type(content_type)


async def get_frontmatter_description_from_file(file_path: Path) -> Optional[str]:
    """Extract description from file's frontmatter.

    Args:
        file_path: Path to file to read

    Returns:
        Description string or None if not found
    """
    content = await read_content_with_frontmatter(file_path)
    return content.frontmatter.get("description")


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
