"""Command discovery utilities for finding and parsing commands in _commands directory."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiofiles
from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.utils.file_discovery import discover_category_files
from mcp_guide.utils.frontmatter import parse_content_with_frontmatter
from mcp_guide.utils.pattern_matching import is_valid_command

logger = get_logger(__name__)

# Simple in-memory cache with thread safety
_command_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_cache_lock = asyncio.Lock()


async def discover_command_files(commands_dir: Path, patterns: List[str]) -> List[Any]:
    """Discover command files, filtering out underscore-prefixed files and directories."""
    all_files = await discover_category_files(commands_dir, patterns)
    # Filter to only include valid command files
    return [file_info for file_info in all_files if is_valid_command(file_info.path)]


async def discover_commands(commands_dir: Path) -> List[Dict[str, Any]]:
    """Discover commands in _commands directory with metadata.

    Args:
        commands_dir: Path to _commands directory

    Returns:
        List of command dictionaries with name, description, usage, examples, etc.
    """
    if not await AsyncPath(commands_dir).exists():
        return []

    # Simple cache key based only on directory path
    # Context is loaded fresh for requirements checking, so no need to include flags in cache key
    # This avoids brittleness from hardcoding specific flag names
    cache_key = str(commands_dir)

    # Load context once for requirements checking
    context_data = None
    try:
        from mcp_guide.utils.template_context_cache import get_template_contexts

        context_data = await get_template_contexts()
    except Exception:
        pass  # Will load later if needed for requirements

    effective_mtime: float = 0.0  # Initialize with default value

    async with _cache_lock:
        # Check if development mode is enabled
        dev_mode = False
        try:
            from mcp_guide.feature_flags.constants import FLAG_GUIDE_DEVELOPMENT
            from mcp_guide.models import resolve_all_flags
            from mcp_guide.session import get_current_session

            session = get_current_session()
            if session:
                flags = await resolve_all_flags(session)
                dev_mode = bool(flags.get(FLAG_GUIDE_DEVELOPMENT, False))
        except Exception:
            # If we can't check the flag, assume production mode (no mtime checks)
            pass

        # In production mode, use cache if available without mtime checks
        if not dev_mode and cache_key in _command_cache:
            return _command_cache[cache_key][1]

        try:
            # Check both directory mtime AND max file mtime (only in dev mode)
            current_mtime = (await AsyncPath(commands_dir).stat()).st_mtime
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
            # Directory access failed, skip cache check and proceed with discovery
            pass

        # Discover command files (excluding underscore-prefixed files)
        files = await discover_command_files(commands_dir, ["**/*"])

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

                parsed = parse_content_with_frontmatter(content)
                front_matter = parsed.frontmatter
                if front_matter:
                    # Check if any requires-* keys exist
                    has_requirements = any(key.startswith("requires-") for key in front_matter.keys())

                    if has_requirements:
                        # Use context loaded earlier (reuse to avoid duplicate calls)
                        if context_data is None:
                            # Context wasn't loaded earlier, load it now
                            from mcp_guide.utils.template_context_cache import get_template_contexts

                            context_data = await get_template_contexts()

                        # Check requirements - skip command if not met
                        from mcp_guide.utils.frontmatter import check_frontmatter_requirements

                        if not check_frontmatter_requirements(front_matter, dict(context_data)):
                            continue

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
                # Cache write failed, continue without caching
                pass

    return commands
