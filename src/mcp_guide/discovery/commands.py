"""Command discovery utilities for finding and parsing commands in _commands directory."""

import asyncio
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import discover_document_files
from mcp_guide.discovery.patterns import is_valid_command
from mcp_guide.render.frontmatter import parse_content_with_frontmatter

logger = get_logger(__name__)

_INVALID_ALIAS_CHARS = set("*?[]<>\\#")


def _is_valid_alias(alias: str) -> bool:
    """Return True when an alias is safe to expose and resolve as a command path."""
    if not alias or alias != alias.strip():
        return False
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in alias):
        return False
    if any(ch in _INVALID_ALIAS_CHARS for ch in alias):
        return False
    if alias.startswith("/") or alias.endswith("/"):
        return False

    segments = alias.split("/")
    if any(not segment or segment in {".", ".."} for segment in segments):
        return False

    return True


def _normalise_aliases(raw_aliases: Any, *, command_name: str, file_path: Path) -> list[str]:
    """Filter invalid aliases from template frontmatter."""
    if not isinstance(raw_aliases, Iterable) or isinstance(raw_aliases, (str, bytes)):
        return []

    aliases: list[str] = []
    for alias in raw_aliases:
        if not isinstance(alias, str) or not _is_valid_alias(alias):
            logger.warning("Ignoring invalid command alias %r in %s for command %s", alias, file_path, command_name)
            continue
        aliases.append(alias)
    return aliases


async def discover_command_files(commands_dir: Path, patterns: list[str]) -> list[Any]:
    """Discover command files, filtering out underscore-prefixed files and directories."""
    all_files = await discover_document_files(commands_dir, patterns)
    # Filter to only include valid command files
    return [file_info for file_info in all_files if is_valid_command(file_info.path)]


async def discover_commands(commands_dir: Path) -> list[dict[str, Any]]:
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
        from mcp_guide.render.cache import get_template_contexts

        context_data = await get_template_contexts()
    except Exception:
        pass  # Will load later if needed for requirements

    effective_mtime: float = 0.0

    # Resolve session first (independent of feature flag availability)
    session = None
    try:
        from mcp_guide.session import get_active_session

        session = get_active_session()
    except Exception:
        pass

    command_cache = session.command_cache if session is not None else None

    # Check if development mode is enabled
    dev_mode = False
    try:
        from mcp_guide.feature_flags.constants import FLAG_GUIDE_DEVELOPMENT
        from mcp_guide.models import resolve_all_flags

        if session:
            flags = await resolve_all_flags(session)
            dev_mode = bool(flags.get(FLAG_GUIDE_DEVELOPMENT, False))
    except Exception:
        pass

    # In production mode, use cache if available without mtime checks
    if command_cache is not None and not dev_mode and cache_key in command_cache:
        return command_cache[cache_key][1]

    effective_mtime: float = 0.0

    # In dev mode, use mtime to invalidate stale cache entries
    if dev_mode and command_cache is not None:
        try:
            current_mtime = (await AsyncPath(commands_dir).stat()).st_mtime

            def _max_file_mtime(base: Path, fallback: float) -> float:
                result = fallback
                for f in base.rglob("*"):
                    if f.is_file():
                        try:
                            result = max(result, f.stat().st_mtime)
                        except OSError:
                            continue
                return result

            effective_mtime = max(
                current_mtime,
                await asyncio.to_thread(_max_file_mtime, commands_dir, current_mtime),
            )

            if cache_key in command_cache:
                cached_mtime, cached_commands = command_cache[cache_key]
                if cached_mtime >= effective_mtime:
                    return cached_commands
        except OSError:
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
            content = await AsyncPath(file_path).read_text(encoding="utf-8")

            parsed = parse_content_with_frontmatter(content)
            front_matter = parsed.frontmatter
            if front_matter:
                # Check if any requires-* keys exist
                has_requirements = any(key.startswith("requires-") for key in front_matter.keys())

                if has_requirements:
                    # Use context loaded earlier (reuse to avoid duplicate calls)
                    if context_data is None:
                        # Context wasn't loaded earlier, load it now
                        from mcp_guide.render.cache import get_template_contexts

                        context_data = await get_template_contexts()

                    # Check requirements - skip command if not met
                    from mcp_guide.render.frontmatter import check_frontmatter_requirements

                    if not check_frontmatter_requirements(front_matter, dict(context_data)):
                        continue

                description = front_matter.get("description", "")
                usage = front_matter.get("usage", "")
                examples = front_matter.get("examples", [])
                aliases = _normalise_aliases(
                    front_matter.get("aliases", []),
                    command_name=command_name,
                    file_path=file_path,
                )
                category = front_matter.get("category", "general")
        except Exception as e:
            # Collect errors for aggregated logging; skip bad files rather than aborting discovery
            error_files.append(f"{file_path}: {e}")
            continue

        commands.append(
            {
                "name": command_name,
                "path": str(commands_dir / file_info.path),  # Make absolute for template use
                "description": description,
                "usage": usage,
                "examples": examples if isinstance(examples, list) else [],
                "aliases": aliases,
                "category": category if isinstance(category, str) else "general",
            }
        )

    # Log aggregated errors once
    if error_files:
        logger.warning(f"Failed to parse {len(error_files)} command files: {'; '.join(error_files[:3])}")
        if len(error_files) > 3:
            logger.warning(f"... and {len(error_files) - 3} more files")

    # Only cache if no errors occurred
    if not error_files and command_cache is not None:
        command_cache[cache_key] = (effective_mtime, commands)

    return commands
