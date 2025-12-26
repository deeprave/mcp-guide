"""File discovery utilities for finding files in category directories."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles.os
from anyio import Path as AsyncPath

from mcp_guide.utils.pattern_matching import safe_glob_search

# Template file extensions
TEMPLATE_EXTENSIONS = (".mustache", ".hbs", ".handlebars", ".chevron")


@dataclass
class FileInfo:
    """File metadata.

    Attributes:
        path: Relative path to file from category directory
        size: File size in bytes including frontmatter
        content_size: Content size in bytes excluding frontmatter
        mtime: File modification time
        name: Relative path without template extension (for agent display)
        content: File content (populated after reading)
        category: Category name where file was discovered (for templating)
        collection: Collection name where file was discovered (for templating)
        ctime: File metadata change time (platform-dependent; Unix: inode change time, Windows: creation time)
    """

    path: Path
    size: int
    content_size: int
    mtime: datetime
    name: str
    content: str | None = None
    frontmatter: Optional[Dict[str, Any]] = None
    category: str | None = None
    collection: str | None = None
    # Platform-dependent metadata change time (Unix: inode change time, Windows: creation time)
    ctime: datetime | None = None


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

    if not await AsyncPath(category_dir).exists() or not await AsyncPath(category_dir).is_dir():
        raise FileNotFoundError(f"Category directory not found: {category_dir}")

    # Validate patterns don't include template extensions
    for pattern in patterns:
        if any(pattern.endswith(ext) for ext in TEMPLATE_EXTENSIONS):
            raise ValueError(
                f"Patterns should not include template extensions {TEMPLATE_EXTENSIONS}: {pattern}. "
                "Template files are automatically discovered."
            )

    # Expand patterns to include extension variants and template variants
    expanded_patterns = []
    for pattern in patterns:
        # Add exact pattern (e.g., "general")
        expanded_patterns.append(pattern)
        # Add pattern with any extension (e.g., "general.*")
        expanded_patterns.append(f"{pattern}.*")
        # Add template variants for all supported extensions
        for ext in TEMPLATE_EXTENSIONS:
            expanded_patterns.append(f"{pattern}{ext}")
            expanded_patterns.append(f"{pattern}.*{ext}")

    matched_paths = await safe_glob_search(category_dir, expanded_patterns)

    # Resolve category_dir for consistent path calculations
    category_dir_resolved = category_dir.resolve()

    # Group by full relative path and prefer non-template over template
    # Note: safe_glob_search returns sorted results, so non-template always comes before template
    files_by_path: dict[str, Path] = {}
    for matched_path in matched_paths:
        relative_path = matched_path.relative_to(category_dir_resolved)

        # Calculate the key: full relative path without template extension
        path_str = str(relative_path)
        key = path_str
        # Remove any template extension to get the base name
        for ext in TEMPLATE_EXTENSIONS:
            if path_str.endswith(ext):
                key = path_str[: -len(ext)]
                break

        # Add if not seen (first occurrence wins, which is non-template due to sorting)
        if key not in files_by_path:
            files_by_path[key] = matched_path

    # Extract metadata for deduplicated files
    results = []
    for matched_path in files_by_path.values():
        stat_result = await aiofiles.os.stat(matched_path)
        relative_path = matched_path.relative_to(category_dir_resolved)

        # Calculate name (full relative path without template extension)
        name = relative_path.as_posix()
        # Remove any template extension to get the display name
        for ext in TEMPLATE_EXTENSIONS:
            if name.endswith(ext):
                name = name[: -len(ext)]
                break

        file_info = FileInfo(
            path=relative_path,
            size=stat_result.st_size,
            content_size=stat_result.st_size,  # Initially same as size, updated after frontmatter processing
            mtime=datetime.fromtimestamp(stat_result.st_mtime),
            name=name,
            ctime=datetime.fromtimestamp(stat_result.st_ctime),
        )
        results.append(file_info)

    return results
