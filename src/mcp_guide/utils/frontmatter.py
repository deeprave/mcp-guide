"""Front-matter parsing utilities for YAML metadata extraction."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiofiles
import yaml

# Content type constants
USER_INFO = "user/information"
AGENT_INFO = "agent/information"
AGENT_INSTRUCTION = "agent/instruction"


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
    content = "\n".join(lines[end_idx + 1 :])

    try:
        metadata = yaml.safe_load(yaml_content)
        return metadata, content
    except yaml.YAMLError:
        return None, content


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
        logging.debug(f"Could not read front-matter from {file_path}: {e}")
        return None, 0
    except yaml.YAMLError as e:
        # Log YAML parsing errors
        logging.debug(f"Could not parse YAML front-matter from {file_path}: {e}")
        return None, 0
    except Exception as e:
        # Log unexpected errors but still return None
        logging.warning(f"Unexpected error parsing front-matter from {file_path}: {e}")
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

    # Case-insensitive lookup for backward compatibility
    for key, value in metadata.items():
        if key.lower() == "description":
            return str(value) if value is not None else None

    return None


def validate_content_type(content_type: Optional[str]) -> bool:
    """Validate if content type is one of the supported types.

    Args:
        content_type: Content type string to validate

    Returns:
        True if valid, False otherwise
    """
    if not content_type:
        return False
    return content_type in (USER_INFO, AGENT_INFO, AGENT_INSTRUCTION)


def get_frontmatter_instruction(frontmatter: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract instruction field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Instruction string or None if not found
    """
    if not frontmatter:
        return None
    return frontmatter.get("instruction")


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
    return str(type_value) if type_value is not None else USER_INFO


def get_frontmatter_partials(frontmatter: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Extract partials field from frontmatter metadata.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Dictionary of partial name to path mappings, empty dict if not found
    """
    if not frontmatter:
        return {}
    partials = frontmatter.get("partials", {})
    if isinstance(partials, dict):
        return {str(k): str(v) for k, v in partials.items()}
    return {}


def get_type_based_default_instruction(content_type: str) -> Optional[str]:
    """Get default instruction based on content type.

    Args:
        content_type: Content type string

    Returns:
        Default instruction string or None for agent/instruction type
    """
    if content_type == USER_INFO:
        return "Display this information to the user"
    elif content_type == AGENT_INFO:
        return "For your information and use. Do not display this content to the user."
    elif content_type == AGENT_INSTRUCTION:
        return None  # Should use explicit instruction from frontmatter
    else:
        # Unknown type defaults to user/information behavior
        return "Display this information to the user"
