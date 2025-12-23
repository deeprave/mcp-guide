"""Command discovery utilities for finding and parsing commands in _commands directory."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiofiles

from mcp_guide.utils.file_discovery import discover_category_files
from mcp_guide.utils.frontmatter import parse_frontmatter_content

logger = logging.getLogger(__name__)

# Simple in-memory cache with thread safety
_command_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_cache_lock = asyncio.Lock()


async def discover_commands(commands_dir: Path) -> List[Dict[str, Any]]:
    """Discover commands in _commands directory with metadata.

    Args:
        commands_dir: Path to _commands directory

    Returns:
        List of command dictionaries with name, description, usage, examples, etc.
    """
    if not commands_dir.exists():
        return []

    cache_key = str(commands_dir)
    effective_mtime: float = 0.0  # Initialize with default value

    async with _cache_lock:
        try:
            # Check both directory mtime AND max file mtime
            current_mtime = commands_dir.stat().st_mtime
            max_file_mtime = max(
                (f.stat().st_mtime for f in commands_dir.rglob("*") if f.is_file()),
                default=current_mtime,
            )
            effective_mtime = max(current_mtime, max_file_mtime)

            if cache_key in _command_cache:
                cached_mtime, cached_commands = _command_cache[cache_key]
                if cached_mtime >= effective_mtime:
                    return cached_commands
        except OSError:
            pass

        # Discover all files in commands directory
        files = await discover_category_files(commands_dir, ["**/*"])

        commands = []
        error_files = []
        for file_info in files:
            # Extract command name from path (remove extension)
            # file_info.path is already relative to commands_dir
            command_name = str(file_info.path.with_suffix(""))

            # Parse front matter by reading file content
            description = ""
            usage = ""
            examples = []
            aliases = []
            category = "general"

            try:
                # Read file content to parse front matter
                file_path = commands_dir / file_info.path
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()

                front_matter, _ = parse_frontmatter_content(content)
                if front_matter:
                    description = front_matter.get("description", "")
                    usage = front_matter.get("usage", "")
                    examples = front_matter.get("examples", [])
                    aliases = front_matter.get("aliases", [])
                    category = front_matter.get("category", "general")
            except Exception as e:
                # Collect error details for aggregated logging
                error_files.append(f"{file_path}: {e}")
                continue

            commands.append(
                {
                    "name": command_name,
                    "path": str(commands_dir / file_info.path),  # Make absolute for template use
                    "description": description,
                    "usage": usage,
                    "examples": examples if isinstance(examples, list) else [],
                    "aliases": aliases if isinstance(aliases, list) else [],
                    "category": category if isinstance(category, str) else "general",
                }
            )

        # Log aggregated errors once
        if error_files:
            logger.warning(f"Failed to parse {len(error_files)} command files: {'; '.join(error_files[:3])}")
            if len(error_files) > 3:
                logger.warning(f"... and {len(error_files) - 3} more files")

        # Only cache if no errors occurred
        if not error_files:
            try:
                _command_cache[cache_key] = (effective_mtime, commands)
            except OSError:
                pass

    return commands
