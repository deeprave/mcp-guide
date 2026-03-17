"""File reading utilities."""

from pathlib import Path

from anyio import Path as AsyncPath


async def read_file_content(file_path: Path) -> str:
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
    return await AsyncPath(file_path).read_text(encoding="utf-8")
