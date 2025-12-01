"""File discovery utilities for finding files in category directories."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiofiles.os

from mcp_guide.utils.pattern_matching import safe_glob_search

# Template file extension
TEMPLATE_EXTENSION = ".mustache"


@dataclass
class FileInfo:
    """File metadata."""

    path: Path
    size: int
    mtime: datetime
    basename: str


async def discover_category_files(
    category_dir: Path,
    patterns: list[str],
) -> list[FileInfo]:
    """Discover files in category directory with metadata.

    Args:
        category_dir: Absolute path to category directory
        patterns: Glob patterns to match files

    Returns:
        List of FileInfo with relative paths, size, mtime

    Raises:
        ValueError: If category_dir is not absolute
        FileNotFoundError: If category_dir doesn't exist
    """
    if not category_dir.is_absolute():
        raise ValueError(f"Category directory must be absolute: {category_dir}")

    if not category_dir.exists() or not category_dir.is_dir():
        raise FileNotFoundError(f"Category directory not found: {category_dir}")

    # Validate patterns don't include template extension
    for pattern in patterns:
        if pattern.endswith(TEMPLATE_EXTENSION):
            raise ValueError(
                f"Patterns should not include {TEMPLATE_EXTENSION} extension: {pattern}. "
                "Template files are automatically discovered."
            )

    # Expand patterns to include template variants
    expanded_patterns = []
    for pattern in patterns:
        expanded_patterns.append(pattern)
        expanded_patterns.append(f"{pattern}{TEMPLATE_EXTENSION}")

    matched_paths = safe_glob_search(category_dir, expanded_patterns)

    # Group by full relative path and prefer non-template over template
    # Note: safe_glob_search returns sorted results, so non-template always comes before template
    files_by_path: dict[str, Path] = {}
    for matched_path in matched_paths:
        relative_path = matched_path.relative_to(category_dir)

        # Calculate the key: full relative path without template extension
        path_str = str(relative_path)
        if path_str.endswith(TEMPLATE_EXTENSION):
            key = path_str[: -len(TEMPLATE_EXTENSION)]
        else:
            key = path_str

        # Add if not seen (first occurrence wins, which is non-template due to sorting)
        if key not in files_by_path:
            files_by_path[key] = matched_path

    # Extract metadata for deduplicated files
    results = []
    for matched_path in files_by_path.values():
        stat_result = await aiofiles.os.stat(matched_path)
        relative_path = matched_path.relative_to(category_dir)

        # Calculate basename (just filename without template extension)
        basename = relative_path.name
        if basename.endswith(TEMPLATE_EXTENSION):
            basename = basename[: -len(TEMPLATE_EXTENSION)]

        file_info = FileInfo(
            path=relative_path,
            size=stat_result.st_size,
            mtime=datetime.fromtimestamp(stat_result.st_mtime),
            basename=basename,
        )
        results.append(file_info)

    return results
