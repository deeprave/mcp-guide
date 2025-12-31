"""Front-matter parsing utilities for YAML metadata extraction."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def parse_frontmatter_content(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Parse YAML front matter from content string.

    Args:
        content: File content string

    Returns:
        Tuple of (metadata_dict, content)
    """
    if not content.startswith("---\n"):
        return None, content

    # Find the closing ---
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, content

    # Extract and parse YAML
    yaml_content = "\n".join(lines[1:end_idx])
    clean_content = "\n".join(lines[end_idx + 1 :])

    try:
        metadata = yaml.safe_load(yaml_content)
        return metadata, clean_content
    except yaml.YAMLError:
        # Even with malformed YAML, strip the frontmatter section
        return None, clean_content


async def extract_frontmatter(file_path: Path, max_read_size: int = 4096) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Extract YAML front-matter from a file.

    Args:
        file_path: Path to the file to read
        max_read_size: Maximum characters to read for front-matter detection

    Returns:
        Tuple of (metadata_dict, frontmatter_length)
        - metadata_dict: Parsed YAML as dict, or None if no front-matter
        - frontmatter_length: Length of front-matter section including delimiters, in characters, or 0
    """
    try:
        # Read only first portion to check for front-matter efficiently
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read(max_read_size)

        # Normalize line endings to handle both \r\n and \n
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Check if file starts with front-matter
        if not content.startswith("---\n"):
            return None, 0

        # Find the end of front-matter
        end_marker = content.find("\n---\n", 4)
        if end_marker == -1:
            return None, 0

        # Extract front-matter content (without delimiters)
        frontmatter_content = content[4:end_marker]

        # Calculate total length including delimiters
        frontmatter_length = end_marker + 5  # "---\n" + content + "\n---\n"

        # Parse YAML front-matter
        metadata = yaml.safe_load(frontmatter_content)
        if not isinstance(metadata, dict):
            return None, 0

        return metadata, frontmatter_length

    except (OSError, UnicodeDecodeError) as e:
        # Log specific I/O and encoding errors but don't fail completely
        logger.debug(f"Could not read front-matter from {file_path}: {e}")
        return None, 0
    except yaml.YAMLError as e:
        # Log YAML parsing errors
        logger.debug(f"Could not parse YAML front-matter from {file_path}: {e}")
        return None, 0
    except Exception as e:
        # Log unexpected errors but still return None
        logger.warning(f"Unexpected error parsing front-matter from {file_path}: {e}")
        return None, 0


async def get_frontmatter_description(file_path: Path) -> Optional[str]:
    """
    Extract description field from YAML front-matter.

    Args:
        file_path: Path to the file to read

    Returns:
        Description string or None if not found
    """
    metadata, _ = await extract_frontmatter(file_path)
    if not metadata:
        return None

    return next(
        (str(value) if value is not None else None for key, value in metadata.items() if key.lower() == "description"),
        None,
    )


def get_frontmatter_instruction(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract instruction field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Instruction string or None if not found
    """
    return frontmatter.get("instruction") if frontmatter else None


def validate_content_type(content_type: Optional[str]) -> bool:
    """Validate if content type is one of the supported types.

    Args:
        content_type: Content type string to validate

    Returns:
        True if valid, False otherwise
    """
    if not content_type:
        return False
    return content_type in (USER_INFO, AGENT_INFO, AGENT_INSTRUCTION, AGENT_REQUIREMENTS)


def get_frontmatter_type(frontmatter: Optional[Dict[str, Any]]) -> str:
    """Extract content type from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Content type string, defaults to USER_INFO if not found
    """
    if not frontmatter:
        return USER_INFO
    type_value = frontmatter.get("type", USER_INFO)
    content_type = str(type_value) if type_value is not None else USER_INFO

    # Validate and warn about unexpected content types
    if not validate_content_type(content_type):
        logger.warning(f"Unknown content type '{content_type}', falling back to '{USER_INFO}'")
        return USER_INFO

    return content_type


def get_frontmatter_includes(frontmatter: Optional[Dict[str, Any]]) -> List[str]:
    """Extract includes field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        List of include paths, empty list if not found
    """

    if not frontmatter:
        logger.debug("No frontmatter provided, returning empty includes")
        return []
    includes = frontmatter.get("includes", [])
    logger.log(5, f"Frontmatter includes detected: {includes}")
    if isinstance(includes, str):
        result = [includes]
        logger.debug(f"Converted string include to list: {result}")
        return result
    elif isinstance(includes, list):
        result = [str(item) for item in includes]
        logger.debug(f"Converted list includes to strings: {result}")
        return result
    logger.debug("No valid includes found, returning empty list")
    return []


def get_type_based_default_instruction(content_type: str) -> Optional[str]:
    """Get default instruction based on content type.

    Args:
        content_type: Content type string

    Returns:
        Default instruction string or None for agent/instruction type
    """

    type_instructions = {
        USER_INFO: INSTRUCTION_DISPLAY_ONLY,
        AGENT_INFO: INSTRUCTION_AGENT_INFO,
        AGENT_INSTRUCTION: INSTRUCTION_AGENT_INSTRUCTIONS,
        AGENT_REQUIREMENTS: INSTRUCTION_AGENT_REQUIREMENTS,
    }

    return type_instructions.get(content_type, INSTRUCTION_DISPLAY_ONLY)
