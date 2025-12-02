"""File reading utilities."""

from pathlib import Path

import aiofiles


async def read_file_content(file_path: Path) -> str:
    """
    Read file content as UTF-8 text asynchronously.

    Reads the entire file content into memory as a UTF-8 encoded string
    without blocking other async tasks.

    Args:
        file_path: Absolute path to the file to read.

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
    async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
        return await f.read()
