"""File reading utilities."""

from pathlib import Path

from anyio import Path as AsyncPath

from mcp_guide.content_limits import ensure_within_limit


async def read_file_content(file_path: Path, *, max_bytes: int | None = None) -> str:
    """
    Read file content as UTF-8 text asynchronously.

    Reads the entire file content into memory as a UTF-8 encoded string
    without blocking other async tasks.

    Args:
        file_path: Path to the file to read (absolute or relative).

    Returns:
        The complete file content as a string. Returns empty string for
        empty files.

    Raises:
        FileNotFoundError: The file does not exist at the specified path.
        PermissionError: Insufficient permissions to read the file.
        UnicodeDecodeError: The file is not valid UTF-8 text (including
            binary files or files with invalid UTF-8 sequences).

    Examples:
        >>> from pathlib import Path
        >>> file = Path("example.txt")
        >>> content = await read_file_content(file)
        >>> print(content)
        Hello, World!

        >>> # Handles Unicode
        >>> content = await read_file_content(Path("unicode.txt"))
        >>> print(content)
        Hello 世界 🌍

        >>> # Raises error for binary files
        >>> await read_file_content(Path("image.png"))
        Traceback (most recent call last):
            ...
        UnicodeDecodeError: ...
    """
    async_path = AsyncPath(file_path)
    if max_bytes is not None:
        # Guide serves static documents.  The preflight is intentionally sufficient:
        # concurrent source-file growth is outside the server's document contract.
        stat = await async_path.stat()
        ensure_within_limit(stat.st_size, limit_name="max-content-limit", limit=max_bytes)
    return await async_path.read_text(encoding="utf-8")
