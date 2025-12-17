"""Front-matter parsing utilities for YAML metadata extraction."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiofiles
import yaml


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
    return metadata.get("description") if metadata else None
