"""Pattern matching utilities for file discovery with security and limits."""

import glob
from pathlib import Path
from typing import List, Set

from mcp_core.mcp_log import get_logger
from mcp_guide.constants import MAX_DOCUMENTS_PER_GLOB, MAX_GLOB_DEPTH, METADATA_SUFFIX

logger = get_logger(__name__)


def is_valid_file(path: Path) -> bool:
    """Check if file should be included in results.

    Args:
        path: File path to check

    Returns:
        True if file is valid, False if should be excluded
    """
    # Check filename
    name = path.name
    if name.startswith(".") or name.startswith("__") or name.endswith(METADATA_SUFFIX):
        return False

    # Check if any parent directory starts with . or __
    return not any(part.startswith(".") or part.startswith("__") for part in path.parts)


def _process_match(
    match_path: Path,
    search_dir: Path,
    seen_files: Set[Path],
    matched_files: List[Path],
) -> bool:
    """Process a single glob match and add to results if valid.

    Returns:
        True if file was added, False otherwise
    """
    if not match_path.is_file():
        return False

    if not is_valid_file(match_path):
        return False

    # Resolve symlinks and deduplicate
    try:
        resolved_path = match_path.resolve()
    except OSError as e:
        logger.warning(f"Failed to resolve symlink {match_path}: {e}")
        return False

    if resolved_path in seen_files:
        return False

    # Check depth limit
    try:
        relative_path = resolved_path.relative_to(search_dir.resolve())
        depth = len(relative_path.parts) - 1  # Subtract 1 for file itself
        if depth > MAX_GLOB_DEPTH:
            return False
    except ValueError:
        # Path is outside search_dir, skip
        logger.debug(f"Skipping file outside search directory: {resolved_path}")
        return False

    matched_files.append(resolved_path)
    seen_files.add(resolved_path)
    return True


def safe_glob_search(search_dir: Path, patterns: List[str]) -> List[Path]:
    """Safely search for files using glob patterns with safety limits.

    Args:
        search_dir: Directory to search within
        patterns: List of glob patterns (e.g., ["*.md", "**/*.py"])

    Returns:
        List of Path objects matching patterns, limited to MAX_DOCUMENTS_PER_GLOB
    """
    matched_files: List[Path] = []
    seen_files: Set[Path] = set()

    for pattern in patterns:
        if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
            logger.warning(f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search")
            break

        pattern_path = search_dir / pattern
        matches_found = False

        # Try original pattern first
        for match_str in glob.iglob(str(pattern_path), recursive=True):
            if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                logger.warning(f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search")
                break

            match_path = Path(match_str)
            if _process_match(match_path, search_dir, seen_files, matched_files):
                matches_found = True

        # If no matches and pattern has no extension, try with .md
        if not matches_found and "." not in Path(pattern).name:
            md_pattern = f"{pattern}.md"
            md_pattern_path = search_dir / md_pattern

            for match_str in glob.iglob(str(md_pattern_path), recursive=True):
                if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                    logger.warning(
                        f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search (.md fallback)"
                    )
                    break

                match_path = Path(match_str)
                _process_match(match_path, search_dir, seen_files, matched_files)

    return matched_files
