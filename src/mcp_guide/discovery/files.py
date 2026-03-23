"""File discovery utilities for finding files in category directories."""

from datetime import datetime
from functools import partial
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Union

if TYPE_CHECKING:
    from mcp_guide.models.project import Category

_SENTINEL = object()  # Sentinel value for distinguishing unset parameters

import anyio
from anyio import Path as AsyncPath

from mcp_guide.discovery.patterns import safe_glob_search
from mcp_guide.store.document_store import get_document_content, list_documents

# Template file extensions
TEMPLATE_EXTENSIONS = (".mustache", ".hbs", ".handlebars", ".chevron")


async def resolve_file_with_extensions(base_path: Path) -> Path | None:
    """Resolve file path trying multiple extension patterns.

    Tries in order:
    1. Exact filename (as is)
    2. <filename>.md
    3. <filename>.<ext> for each ext in TEMPLATE_EXTENSIONS
    4. <filename>.md.<ext> for each ext in TEMPLATE_EXTENSIONS

    Args:
        base_path: Base path without extension

    Returns:
        Resolved path if found, None otherwise
    """
    # Try exact filename first
    if await AsyncPath(base_path).exists():
        return base_path

    # Try .md
    md_path = base_path.with_suffix(".md")
    if await AsyncPath(md_path).exists():
        return md_path

    # Try template extensions
    for ext in TEMPLATE_EXTENSIONS:
        ext_path = base_path.with_suffix(ext)
        if await AsyncPath(ext_path).exists():
            return ext_path

    # Try .md + template extensions
    for ext in TEMPLATE_EXTENSIONS:
        md_ext_path = base_path.with_suffix(f".md{ext}")
        if await AsyncPath(md_ext_path).exists():
            return md_ext_path

    return None


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
        path: Relative or absolute path to file. Initially relative to category directory,
              but may be converted to absolute during deduplication to correctly identify
              files with the same name across different categories.
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

    def resolve(self, base_dir: Path, docroot: Path) -> Path:
        """Resolve relative path to absolute path with security validation.

        Args:
            base_dir: Base directory to resolve relative paths against
            docroot: Document root directory for security validation

        Returns:
            Resolved absolute path within docroot

        Raises:
            ValueError: If base_dir or docroot are not absolute
            ValueError: If base_dir is not within docroot
            ValueError: If resolved path escapes docroot
        """
        # Validate inputs are absolute
        if not base_dir.is_absolute():
            raise ValueError(f"Base directory must be absolute: {base_dir}")
        if not docroot.is_absolute():
            raise ValueError(f"Document root must be absolute: {docroot}")

        # Validate base_dir is within docroot
        from mcp_guide.core.path_security import is_path_within_directory

        if not is_path_within_directory(base_dir, docroot):
            raise ValueError(f"Base directory must be within docroot: {base_dir}")

        # Resolve path
        if not self.path.is_absolute():
            self.path = base_dir / self.path

        resolved = self.path.resolve()

        # Validate resolved path is within docroot
        if not is_path_within_directory(resolved, docroot):
            raise ValueError(f"Resolved path escapes docroot: {resolved}")

        self.path = resolved
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

    async def read_raw(self) -> str:
        """Read raw content from source without frontmatter processing.

        Uses content_loader for stored documents, filesystem for files.

        Returns:
            Raw content string

        Raises:
            FileNotFoundError: If file doesn't exist or loader returns None
            OSError: If content cannot be loaded from the filesystem
            Exception: Any exception from content_loader is propagated
        """
        if self._content_loader is not None:
            content = await self._content_loader()
            if content is None:
                raise FileNotFoundError(f"No content available for {self.path}")
            return content
        from mcp_guide.core import read_file_content

        return await read_file_content(self.path)

    def _parse_frontmatter_if_needed(self) -> None:
        """Internal method to parse frontmatter if not already parsed."""
        if self._frontmatter is not None or self._content is None:
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
) -> list[FileInfo]:
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
        loader = partial(get_document_content, record.category, record.name)
        results.append(
            FileInfo(
                path=Path(record.name),
                size=0,
                content_size=0,
                mtime=mtime,
                name=record.name,
                ctime=datetime.fromisoformat(record.created_at),
                content_loader=loader,
                source="store",
            )
        )
    return results


async def discover_documents(
    base_dir: Path,
    patterns: list[str],
    category: Optional[str] = None,
) -> list[FileInfo]:
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

    file_results: list[FileInfo] = []
    store_results: list[FileInfo] = []

    async with anyio.create_task_group() as tg:

        async def _files() -> None:
            file_results.extend(await discover_document_files(base_dir, patterns))

        async def _stored() -> None:
            store_results.extend(await discover_document_stored(category, patterns))

        tg.start_soon(_files)
        tg.start_soon(_stored)

    return file_results + store_results


async def discover_document_files(
    base_dir: Path,
    patterns: list[str],
) -> list[FileInfo]:
    """Discover files in directory with metadata.

    Args:
        base_dir: Absolute path to base directory
        patterns: Glob patterns to match files

    Returns:
        List of FileInfo with relative paths, size, mtime

    Raises:
        ValueError: If base_dir is not absolute
        FileNotFoundError: If base_dir doesn't exist
    """
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

    # Expand patterns to include extension variants and template variants
    expanded_patterns: list[str] = []
    for pattern in patterns:
        expanded_patterns.extend(get_file_extension_patterns(pattern))
    matched_paths = await safe_glob_search(base_dir, expanded_patterns)

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

    return results
