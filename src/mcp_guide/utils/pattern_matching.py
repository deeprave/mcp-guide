"""Pattern matching utilities for file discovery with security and limits."""

import fnmatch
import glob
import logging
import os
from pathlib import Path
from typing import List, Set

from mcp_guide.constants import MAX_DOCUMENTS_PER_GLOB, MAX_GLOB_DEPTH, METADATA_SUFFIX

logger = logging.getLogger(__name__)


def is_valid_file(path: Path) -> bool:
    """Check if file should be included in results.

    Args:
        path: File path to check

    Returns:
        True if file is valid, False if should be excluded
    """
    # Check filename - exclude metadata files, __pycache__ style names, and hidden files
    name = path.name
    if name.startswith("__") or name.endswith(METADATA_SUFFIX) or name.startswith("."):
        return False

    # Check if any parent directory starts with . or __ (hidden or special directories)
    return not any(part in (".", "..") or part.startswith("__") or part.startswith(".") for part in path.parts)


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


def _walk_with_depth_limit(search_dir: Path, pattern: str) -> List[Path]:
    """Walk directory tree with depth limit, matching pattern.

    Uses os.walk() with manual depth tracking to prevent DOS from deep traversal.
    Only traverses up to MAX_GLOB_DEPTH levels.
    """
    matched_paths: List[Path] = []
    search_dir_resolved = search_dir.resolve()

    # Check if pattern contains ** (recursive)
    if "**" not in pattern:
        # Non-recursive: use glob directly (safe, only checks one level)
        pattern_path = search_dir / pattern
        for match_str in glob.iglob(str(pattern_path), recursive=False):
            matched_paths.append(Path(match_str))
        return matched_paths

    # Recursive pattern: use os.walk with depth limit
    # Parse pattern to extract directory prefix and file pattern
    # Examples:
    #   "**/*.md" -> prefix="", file_pattern="*.md"
    #   "docs/**/*.py" -> prefix="docs", file_pattern="*.py"
    #   "**/*" -> prefix="", file_pattern="*"

    pattern_parts = pattern.split("**/")
    if len(pattern_parts) == 2:
        prefix = pattern_parts[0].rstrip("/")
        file_pattern = pattern_parts[1] if pattern_parts[1] else "*"
    elif pattern.startswith("**/"):
        prefix = ""
        file_pattern = pattern[3:] if len(pattern) > 3 else "*"
    else:
        # Pattern like "**" alone
        prefix = ""
        file_pattern = "*"

    start_dir = search_dir / prefix if prefix else search_dir

    if not start_dir.exists():
        return matched_paths

    for root, dirs, files in os.walk(start_dir):
        root_path = Path(root).resolve()  # Resolve to handle symlinks

        # Calculate depth relative to search_dir
        try:
            relative = root_path.relative_to(search_dir_resolved)
            depth = len(relative.parts)
        except ValueError:
            # Outside search_dir, skip
            continue

        # Stop traversing deeper if we've hit the limit
        if depth >= MAX_GLOB_DEPTH:
            dirs.clear()  # Don't descend into subdirectories

        # Match files in this directory
        for filename in files:
            if fnmatch.fnmatch(filename, file_pattern):
                matched_paths.append(root_path / filename)

    return matched_paths


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

        matches_found = False

        # Use depth-limited walk for safety
        try:
            candidate_paths = _walk_with_depth_limit(search_dir, pattern)
        except Exception as e:
            logger.warning(f"Pattern '{pattern}' failed: {e}")
            continue

        for match_path in candidate_paths:
            if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                logger.warning(f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search")
                break

            if _process_match(match_path, search_dir, seen_files, matched_files):
                matches_found = True

        # If no matches and pattern has no extension, try with .md
        if not matches_found and "." not in Path(pattern).name:
            md_pattern = f"{pattern}.md"

            try:
                candidate_paths = _walk_with_depth_limit(search_dir, md_pattern)
            except Exception as e:
                logger.warning(f"Pattern '{md_pattern}' failed: {e}")
                continue

            for match_path in candidate_paths:
                if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                    logger.warning(
                        f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search (.md fallback)"
                    )
                    break

                _process_match(match_path, search_dir, seen_files, matched_files)

    return matched_files
