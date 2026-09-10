"""Pattern matching utilities for file discovery with security and limits."""

import fnmatch
import glob
import heapq
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import List, Set

from anyio import Path as AsyncPath

from mcp_guide.config_constants import (
    COMMANDS_DIR,
    MAX_DOCUMENTS_PER_GLOB,
    MAX_GLOB_DEPTH,
    MAX_GLOB_DIRECTORY_ENTRIES,
    MAX_GLOB_ENTRIES,
    MAX_GLOB_ENUMERATION_SECONDS,
    MAX_GLOB_PATTERNS,
)
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.lazy_path import LazyPath

logger = get_logger(__name__)


@dataclass
class GlobSearchResult:
    """Bounded glob matches with guards that truncated discovery."""

    paths: list[Path]
    truncation_reasons: set[str] = field(default_factory=set)

    def __iter__(self):
        return iter(self.paths)

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> Path:
        return self.paths[index]

    def __eq__(self, other: object) -> bool:
        return self.paths == other


@dataclass
class _TraversalState:
    """Mutable accounting shared by all patterns in one glob search."""

    truncation_reasons: set[str]
    inspected_entries: int = 0
    enumeration_seconds: float = 0.0

    @property
    def stopped(self) -> bool:
        return bool(self.truncation_reasons & {"aggregate entry count", "enumeration time"})

    def truncate(self, reason: str) -> None:
        """Record and log a traversal guard the first time it is reached."""
        if reason not in self.truncation_reasons:
            self.truncation_reasons.add(reason)
            logger.warning("Glob discovery truncated by %s", reason)


def is_valid_file(path: Path) -> bool:
    """Check if file should be included in results.

    Args:
        path: File path to check

    Returns:
        True if file is valid, False if should be excluded
    """
    # Check filename - exclude __pycache__ style names, hidden files, and backup files
    name = path.name
    if name.startswith("__") or name.startswith(".") or name.endswith(".orig"):
        return False

    # Check parent directories for __pycache__ style directories and reject . and .. segments
    for part in path.parts[:-1]:  # Exclude filename from check
        if part.startswith("__") or part in (".", ".."):
            return False

    return True


def is_valid_command(path: Path) -> bool:
    """Check if file should be considered a valid command.

    Args:
        path: File path to check

    Returns:
        True if file is a valid command, False if should be excluded
    """
    # First apply general file validity rules
    if not is_valid_file(path):
        return False

    # Command-specific rules: exclude underscore-prefixed files
    name = path.name
    if name.startswith("_"):
        return False

    # Check path components for underscore prefixes, but allow _commands directory
    for i, part in enumerate(path.parts[:-1]):  # Exclude filename from check
        if part.startswith("_"):
            # Allow _commands as the first underscore directory (official commands dir)
            if part == COMMANDS_DIR:
                continue
            return False

    return True


async def _process_match(
    match_path: Path,
    search_dir: Path,
    seen_files: Set[Path],
    matched_files: List[Path],
) -> bool:
    """Process a single glob match and add to results if valid.

    Uses resolved paths only for deduplication (so symlinks to the same
    target aren't counted twice), but stores the original unresolved path.

    Returns:
        True if file was added, False otherwise
    """
    if not await AsyncPath(match_path).is_file():
        return False

    if not is_valid_file(match_path):
        return False

    # Resolve only for deduplication
    try:
        resolved_path = match_path.resolve()
    except (OSError, RuntimeError) as e:
        logger.warning(f"Failed to resolve symlink {match_path}: {e}")
        return False

    if resolved_path in seen_files:
        return False

    # Check depth limit using the unresolved path
    try:
        relative_path = match_path.relative_to(search_dir)
        depth = len(relative_path.parts) - 1  # Subtract 1 for file itself
        if depth > MAX_GLOB_DEPTH:
            return False
    except ValueError:
        logger.debug(f"Skipping file outside search directory: {match_path}")
        return False

    matched_files.append(match_path)
    seen_files.add(resolved_path)
    return True


def _read_directory_entries(path: Path, state: _TraversalState) -> list[os.DirEntry[str]]:
    """Read one bounded directory prefix in canonical entry-name order."""
    entries: list[os.DirEntry[str]] = []
    try:
        with os.scandir(path) as iterator:
            while len(entries) < MAX_GLOB_DIRECTORY_ENTRIES:
                started = monotonic()
                try:
                    entry = next(iterator)
                except StopIteration:
                    break
                state.enumeration_seconds += monotonic() - started
                state.inspected_entries += 1
                entries.append(entry)
                if state.enumeration_seconds >= MAX_GLOB_ENUMERATION_SECONDS:
                    state.truncate("enumeration time")
                    break
                if state.inspected_entries >= MAX_GLOB_ENTRIES:
                    state.truncate("aggregate entry count")
                    break
            else:
                try:
                    next(iterator)
                except StopIteration:
                    pass
                else:
                    state.truncate("directory entry count")
    except OSError as error:
        logger.warning("Failed to enumerate path %s during glob discovery: %s", path, error)
    return sorted(entries, key=lambda item: item.name)


async def _iter_recursive_matches(search_dir: Path, pattern: str, state: _TraversalState) -> AsyncIterator[Path]:
    """Yield recursive matches in canonical relative-path order without a tree-wide list."""
    prefix, _, suffix = pattern.partition("**/")
    if pattern == "**":
        prefix, suffix = "", "*"
    start_dir = search_dir / prefix.rstrip("/") if prefix else search_dir
    file_pattern = suffix or "*"
    if not await AsyncPath(start_dir).exists():
        return

    pending: list[tuple[str, int, Path, bool]] = [
        (start_dir.relative_to(search_dir).as_posix() + "/", 0, start_dir, True)
    ]
    sequence = 1
    visited_dirs: set[Path] = set()
    while pending:
        _, _, path, is_directory = heapq.heappop(pending)
        if not is_directory:
            yield path
            continue
        if state.stopped:
            continue
        try:
            resolved = path.resolve()
            if resolved in visited_dirs:
                continue
            visited_dirs.add(resolved)
            depth = len(path.relative_to(search_dir).parts)
        except (OSError, RuntimeError, ValueError):
            logger.warning("Failed to resolve path %s during glob discovery; skipping", path)
            continue

        for entry in _read_directory_entries(path, state):
            entry_path = Path(entry.path)
            try:
                directory = entry.is_dir(follow_symlinks=True)
            except OSError:
                continue
            if directory:
                if depth >= MAX_GLOB_DEPTH:
                    state.truncate("depth")
                    continue
                key = entry_path.relative_to(search_dir).as_posix() + "/"
                heapq.heappush(pending, (key, sequence, entry_path, True))
                sequence += 1
            elif fnmatch.fnmatch(entry.name, file_pattern):
                key = entry_path.relative_to(search_dir).as_posix()
                heapq.heappush(pending, (key, sequence, entry_path, False))
                sequence += 1


async def _iter_non_recursive_matches(search_dir: Path, pattern: str, state: _TraversalState) -> AsyncIterator[Path]:
    """Yield a bounded, canonically sorted non-recursive glob stream."""
    parent_pattern, separator, file_pattern = pattern.rpartition("/")
    parent_parts = parent_pattern.split("/") if separator else []
    directories = [search_dir]

    for part in parent_parts:
        if not part or part == ".":
            continue
        next_directories: list[Path] = []
        for directory in directories:
            if state.stopped:
                break
            if glob.has_magic(part):
                for entry in _read_directory_entries(directory, state):
                    try:
                        if entry.is_dir(follow_symlinks=True) and fnmatch.fnmatch(entry.name, part):
                            next_directories.append(Path(entry.path))
                    except OSError:
                        continue
            else:
                candidate = directory / part
                if await AsyncPath(candidate).is_dir():
                    next_directories.append(candidate)
        directories = sorted(next_directories, key=lambda path: path.relative_to(search_dir).as_posix())

    directory_matches: list[list[Path]] = []
    for directory in directories:
        if state.stopped:
            break
        matches: list[Path] = []
        for entry in _read_directory_entries(directory, state):
            try:
                if not entry.is_dir(follow_symlinks=True) and fnmatch.fnmatch(entry.name, file_pattern):
                    matches.append(Path(entry.path))
            except OSError:
                continue
        if matches:
            directory_matches.append(matches)

    pending: list[tuple[str, int, int, Path]] = []
    for directory_index, matches in enumerate(directory_matches):
        path = matches[0]
        heapq.heappush(pending, (path.relative_to(search_dir).as_posix(), directory_index, 0, path))
    while pending:
        _, directory_index, match_index, path = heapq.heappop(pending)
        yield path
        next_index = match_index + 1
        matches = directory_matches[directory_index]
        if next_index < len(matches):
            next_path = matches[next_index]
            heapq.heappush(
                pending,
                (next_path.relative_to(search_dir).as_posix(), directory_index, next_index, next_path),
            )


async def safe_glob_search(search_dir: Path, patterns: List[str], *, limit_patterns: bool = True) -> GlobSearchResult:
    """Safely search for files using glob patterns with safety limits.

    Args:
        search_dir: Directory to search within
        patterns: List of glob patterns (e.g., ["*.md", "**/*.py"])

    Returns:
        Bounded matching paths and any guards that truncated discovery
    """
    # Expand ~ and ${VAR} without resolving symlinks
    search_dir_expanded = LazyPath(search_dir).expand()

    matched_files: List[Path] = []
    seen_files: Set[Path] = set()
    truncation_reasons: set[str] = set()
    state = _TraversalState(truncation_reasons)

    if limit_patterns and len(patterns) > MAX_GLOB_PATTERNS:
        state.truncate("pattern count")
        patterns = patterns[:MAX_GLOB_PATTERNS]

    for pattern in patterns:
        if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
            logger.warning(f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search")
            break

        matches_found = False

        if "**" in pattern:
            candidates = _iter_recursive_matches(search_dir_expanded, pattern, state)
        else:
            candidates = _iter_non_recursive_matches(search_dir_expanded, pattern, state)
        async for match_path in candidates:
            if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                logger.warning(f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search")
                break

            if await _process_match(match_path, search_dir_expanded, seen_files, matched_files):
                matches_found = True

        # If no matches and pattern has no extension, try with .* wildcard
        if not matches_found and "." not in Path(pattern).name:
            wildcard_pattern = f"{pattern}.*"

            if "**" in wildcard_pattern:
                fallback_candidates = _iter_recursive_matches(search_dir_expanded, wildcard_pattern, state)
            else:
                fallback_candidates = _iter_non_recursive_matches(search_dir_expanded, wildcard_pattern, state)
            async for match_path in fallback_candidates:
                if len(matched_files) >= MAX_DOCUMENTS_PER_GLOB:
                    logger.warning(
                        f"Reached maximum document limit ({MAX_DOCUMENTS_PER_GLOB}) for glob search (.* fallback)"
                    )
                    break

                await _process_match(match_path, search_dir_expanded, seen_files, matched_files)

    return GlobSearchResult(sorted(matched_files, key=lambda path: path.as_posix()), truncation_reasons)
