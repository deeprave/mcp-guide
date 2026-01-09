"""Client path resolution utilities for MCP server context."""

from pathlib import Path
from typing import Union


def client_resolve(path: Union[str, Path], client_cwd: Union[str, Path]) -> Path:
    """Resolve a path relative to the client's working directory.

    This function handles path resolution from the server's perspective when
    dealing with client filesystem paths. The server cannot use Path.resolve()
    directly since it doesn't have access to the client's filesystem.

    Args:
        path: Path to resolve (relative or absolute)
        client_cwd: Client's current working directory

    Returns:
        Absolute Path object representing the resolved client path

    Examples:
        >>> client_resolve(".guide.yaml", "/home/username/project")
        PosixPath('/home/username/project/.guide.yaml')

        >>> client_resolve("../config.json", "/home/username/project")
        PosixPath('/home/username/config.json')

        >>> client_resolve("/absolute/path.txt", "/home/username/project")
        PosixPath('/absolute/path.txt')
    """
    path_obj = Path(path)
    client_cwd_obj = Path(client_cwd)

    if path_obj.is_absolute():
        return path_obj
    else:
        return client_cwd_obj / path_obj
