"""File discovery utilities for finding files in category directories."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Union

if TYPE_CHECKING:
    from mcp_guide.models.project import Category
    from mcp_guide.render.cache_policy import CachePolicy
    from mcp_guide.render.document_properties import DocumentProperties

_SENTINEL = object()  # Sentinel value for distinguishing unset parameters

import anyio
from anyio import Path as AsyncPath

from mcp_guide.config_constants import MAX_GLOB_PATTERNS
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.patterns import safe_glob_search
from mcp_guide.lazy_path import LazyPath
from mcp_guide.store.document_store import get_document_content, list_documents

# Template file extensions
TEMPLATE_EXTENSIONS = (".mustache", ".hbs", ".handlebars", ".chevron")
logger = get_logger(__name__)


class FileInfoList(list["FileInfo"]):
    """Discovered files with any filesystem truncation diagnostics."""

    def __init__(self, files: list["FileInfo"] | None = None, truncation_reasons: set[str] | None = None):
        super().__init__(files or [])
        self.truncation_reasons = truncation_reasons or set()


def get_file_extension_patterns(base_pattern: str) -> list[str]:
    """Get all file extension patterns for a base pattern.

    Returns patterns for:
    1. base_pattern (exact)
    2. base_pattern.* (any extension)
    3. base_pattern<ext> for each TEMPLATE_EXTENSION
    4. base_pattern.*<ext> for each TEMPLATE_EXTENSION

    Args:
        base_pattern: Base pattern without extensions

    Returns:
        List of glob patterns to try
    """
    patterns = [base_pattern, f"{base_pattern}.*"]

    # Add template variants for all supported extensions
    for ext in TEMPLATE_EXTENSIONS:
        patterns.extend([f"{base_pattern}{ext}", f"{base_pattern}.*{ext}"])

    return patterns


class FileInfo:
    """File metadata.

    Attributes:
        path: Relative or absolute path to file. Initially relative to the category
              directory. ``resolve()`` stores the host-absolute document path so later
              calls can skip the relative join and still re-check containment.
        size: File size in bytes including frontmatter
        content_size: Content size in bytes excluding frontmatter
        mtime: File modification time
        name: Relative path without template extension (for agent display)
        category: Category object for accessing directory and configuration
        ctime: File metadata change time (platform-dependent; Unix: inode change time, Windows: creation time)
        source: Content origin identifier (e.g. "file", "store")
        content_loader: Optional async callback for loading content from non-filesystem sources
    """

    def __init__(
        self,
        path: Path,
        size: int,
        content_size: int,
        mtime: datetime,
        name: str,
        category: Optional["Category"] = None,
        ctime: Optional[datetime] = None,
        content: Union[str, None, object] = _SENTINEL,
        frontmatter: Optional[Dict[str, Any]] = None,
        content_loader: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
        source: str = "file",
    ):
        """Initialize FileInfo with optional legacy content and frontmatter parameters."""
        self.path = path
        self.size = size
        self.content_size = content_size
        self.mtime = mtime
        self.name = name
        self.category = category
        self.ctime = ctime
        self.source = source
        self._content_loader = content_loader

        # Private attributes for lazy loading
        if content is _SENTINEL:
            self._content: Optional[str] = None
        else:
            self._content = content  # ty: ignore[invalid-assignment]
        self._frontmatter = frontmatter
        self._load_error: Optional[str] = None
        # Track if content was explicitly provided (even if None)
        self._content_explicitly_set = content is not _SENTINEL
        self._raw_cache: Optional[str] = None
        self.cache_policy: CachePolicy | None = None
        self.document_properties: DocumentProperties | None = None

    def resolve(self, resolver: Callable[[str | Path], Path], relative_dir: str | Path = "") -> Path:
        """Resolve this file through a document-root-relative path resolver.

        Args:
            resolver: Sync lexical resolver from RequestContext
            relative_dir: Optional directory relative to the document root

        Returns:
            Absolute lexical path within the document root

        Raises:
            ValueError: If the path escapes the document root
        """
        if LazyPath(self.path).is_absolute():
            self.path = resolver(LazyPath(self.path).resolve())
            return self.path
        relative: str | Path = self.path
        if relative_dir not in ("", ".", Path(""), Path(".")):
            relative = Path(relative_dir) / self.path
        self.path = resolver(relative)
        return self.path

    async def _load_content_if_needed(self) -> None:
        """Internal method to load content if not already loaded."""
        # If content was explicitly set (even to None), don't try to load
        if self._content_explicitly_set:
            return

        if self._content is not None:
            return

        # Try content_loader first (e.g. from document store)
        if self._content_loader is not None:
            self._content = await self._content_loader()
            if self._content is not None:
                self.size = len(self._content)
            self._load_error = None
            return

        # Fall back to filesystem read
        from mcp_guide.core import read_file_content

        try:
            self._content = await read_file_content(self.path)
            if self._content is not None:
                self.size = len(self._content)
            self._load_error = None
        except (OSError, PermissionError, FileNotFoundError) as e:
            self._content = None
            self._load_error = str(e)

    async def read_raw(self, *, max_bytes: int | None = None) -> str:
        """Read raw content from source without frontmatter processing.

        Uses content_loader for stored documents, filesystem for files.
        Result is cached so repeated calls do not trigger additional reads.

        Returns:
            Raw content string

        Raises:
            FileNotFoundError: If file doesn't exist or loader returns None
            OSError: If content cannot be loaded from the filesystem
            Exception: Any exception from content_loader is propagated
        """
        if self._raw_cache is not None:
            if max_bytes is not None:
                from mcp_guide.content_limits import ensure_within_limit

                ensure_within_limit(
                    len(self._raw_cache.encode("utf-8")), limit_name="max-content-limit", limit=max_bytes
                )
            return self._raw_cache
        if max_bytes is not None:
            from mcp_guide.content_limits import ensure_within_limit

            ensure_within_limit(self.size, limit_name="max-content-limit", limit=max_bytes)
        if self._content_loader is not None:
            content = await self._content_loader()
            if content is None:
                raise FileNotFoundError(f"No content available for {self.path}")
            self._raw_cache = content
            return content
        from mcp_guide.core import read_file_content

        result = await read_file_content(self.path, max_bytes=max_bytes)
        self._raw_cache = result
        return result

    def _parse_frontmatter_if_needed(self) -> None:
        """Internal method to parse frontmatter if not already parsed."""
        if self._frontmatter is not None or self._content is None or self.source == "store":
            return

        from mcp_guide.render.frontmatter import parse_content_with_frontmatter

        parsed = parse_content_with_frontmatter(self._content)
        self._frontmatter = parsed.frontmatter
        self._content = parsed.content
        if self._content is not None:
            self.content_size = len(self._content)

    async def get_content(self) -> Optional[str]:
        """Get file content, loading and parsing if needed."""
        await self._load_content_if_needed()
        if hasattr(self, "_load_error") and self._load_error:
            raise OSError(f"Error reading file {self.path}: {self._load_error}")
        self._parse_frontmatter_if_needed()
        return self._content

    async def get_frontmatter(self) -> Optional[Dict[str, Any]]:
        """Get frontmatter, loading and parsing if needed."""
        await self._load_content_if_needed()
        if hasattr(self, "_load_error") and self._load_error:
            raise OSError(f"Error reading file {self.path}: {self._load_error}")
        self._parse_frontmatter_if_needed()
        return self._frontmatter

    # Temporary synchronous accessors for backward compatibility
    # These should only be used when content is already loaded
    @property
    def content(self) -> Optional[str]:
        """Synchronous access to content (only use when already loaded)."""
        return self._content

    @content.setter
    def content(self, value: Optional[str]) -> None:
        """Set content directly."""
        self._content = value
        if value is not None:
            self.size = len(value)

    @property
    def frontmatter(self) -> Optional[Dict[str, Any]]:
        """Synchronous access to frontmatter (only use when already loaded)."""
        return self._frontmatter

    @frontmatter.setter
    def frontmatter(self, value: Optional[Dict[str, Any]]) -> None:
        """Set frontmatter directly."""
        self._frontmatter = value


async def discover_document_stored(
    category: str,
    patterns: list[str],
    max_content_limit: int | None = None,
) -> FileInfoList:
    """Discover documents from the document store.

    Uses the same pattern expansion as filesystem discovery
    (get_file_extension_patterns) including template extension variants.
    Matching is case-sensitive, consistent with filesystem behaviour.

    Args:
        category: Category name to query
        patterns: Glob patterns to filter document names

    Returns:
        List of FileInfo with content_loader and source="store"
    """
    expanded: list[str] = []
    for p in patterns:
        expanded.extend(get_file_extension_patterns(p))

    records = await list_documents(category)
    results = []
    for record in records:
        if not any(PurePosixPath(record.name).full_match(ep) for ep in expanded):
            continue
        mtime = datetime.fromisoformat(record.updated_at)
        loader = partial(get_document_content, record.category, record.name, max_content_limit=max_content_limit)
        results.append(
            FileInfo(
                path=Path(record.name),
                size=record.content_size,
                content_size=record.content_size,
                mtime=mtime,
                name=record.name,
                ctime=datetime.fromisoformat(record.created_at),
                content_loader=loader,
                source="store",
                frontmatter=record.metadata or {},
            )
        )
    return FileInfoList(results)


async def discover_documents(
    base_dir: Path,
    patterns: list[str],
    category: Optional[str] = None,
    max_content_limit: int | None = None,
) -> FileInfoList:
    """Discover documents from filesystem and optionally the document store.

    Args:
        base_dir: Absolute path to base directory for filesystem discovery
        patterns: Glob patterns to match files
        category: If provided, also query the document store for this category

    Returns:
        Combined list of FileInfo from both sources
    """
    # No cross-source deduplication: filesystem files and stored documents are
    # distinct by design. The store's uniqueness constraint prevents duplicates
    # within the store, and users do not store existing category files.
    if category is None:
        return await discover_document_files(base_dir, patterns)

    file_results = FileInfoList()
    store_results: list[FileInfo] = []

    async with anyio.create_task_group() as tg:

        async def _files() -> None:
            discovered_files = await discover_document_files(base_dir, patterns)
            file_results.extend(discovered_files)
            file_results.truncation_reasons.update(discovered_files.truncation_reasons)

        async def _stored() -> None:
            store_results.extend(await discover_document_stored(category, patterns, max_content_limit))

        tg.start_soon(_files)
        tg.start_soon(_stored)

    return FileInfoList(file_results + store_results, file_results.truncation_reasons)


async def discover_document_files(
    base_dir: Path,
    patterns: list[str],
) -> FileInfoList:
    """Discover files in directory with metadata.

    Args:
        base_dir: Base directory. ``~``, ``$VAR``, and relative paths are
            resolved at use time through ``LazyPath.resolve()``.
        patterns: Glob patterns to match files

    Returns:
        List of FileInfo with relative paths, size, mtime

    Raises:
        ValueError: If base_dir is not absolute after resolution
        FileNotFoundError: If base_dir doesn't exist
    """
    base_dir = LazyPath(base_dir).resolve()
    if not base_dir.is_absolute():
        raise ValueError(f"Base directory must be absolute: {base_dir}")

    if not await AsyncPath(base_dir).exists() or not await AsyncPath(base_dir).is_dir():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")

    # Validate patterns don't include template extensions
    for pattern in patterns:
        if any(pattern.endswith(ext) for ext in TEMPLATE_EXTENSIONS):
            raise ValueError(
                f"Patterns should not include template extensions {TEMPLATE_EXTENSIONS}: {pattern}. "
                "Template files are automatically discovered."
            )

    truncated_patterns = len(patterns) > MAX_GLOB_PATTERNS
    if truncated_patterns:
        logger.warning("Glob discovery truncated by pattern count")
        patterns = patterns[:MAX_GLOB_PATTERNS]

    # Extension variants belong to each accepted original expression.
    expanded_patterns: list[str] = []
    for pattern in patterns:
        expanded_patterns.extend(get_file_extension_patterns(pattern))
    matched_paths = await safe_glob_search(base_dir, expanded_patterns, limit_patterns=False)
    if truncated_patterns:
        matched_paths.truncation_reasons.add("pattern count")

    # Group by full relative path and prefer non-template over template
    # Note: safe_glob_search returns sorted results, so non-template always comes before template
    files_by_path: dict[str, Path] = {}
    for matched_path in matched_paths:
        relative_path = matched_path.relative_to(base_dir)

        # Calculate the key: full relative path without template extension
        path_str = str(relative_path)
        key = next(
            (path_str[: -len(ext)] for ext in TEMPLATE_EXTENSIONS if path_str.endswith(ext)),
            path_str,
        )
        # Add if not seen (first occurrence wins, which is non-template due to sorting)
        if key not in files_by_path:
            files_by_path[key] = matched_path

    # Extract metadata for deduplicated files
    results = []
    for matched_path in files_by_path.values():
        stat_result = await AsyncPath(matched_path).stat()
        relative_path = matched_path.relative_to(base_dir)

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

    return FileInfoList(results, matched_paths.truncation_reasons)
