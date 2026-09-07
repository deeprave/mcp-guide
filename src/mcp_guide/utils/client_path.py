"""Client path resolution utilities for MCP server context."""

from pathlib import Path
from typing import Union

from mcp_guide.lazy_path import LazyPath


def client_resolve(path: Union[str, Path], client_cwd: Union[str, Path]) -> Path:
    """Resolve a path relative to the client's working directory.

    Delegates to LazyPath's process-wide client policy. Relative paths and
    user/environment expansion require verified sharing; otherwise input must be
    absolute and is normalised without server filesystem access.

    Args:
        path: Path to resolve (relative or absolute)
        client_cwd: Client's current working directory

    Returns:
        Absolute Path object representing the resolved client path

    Examples (with verified sharing):
        >>> client_resolve(".guide.yaml", "/home/username/project")
        PosixPath('/home/username/project/.guide.yaml')

        >>> client_resolve("../config.json", "/home/username/project")
        PosixPath('/home/username/config.json')

        >>> client_resolve("/absolute/path.txt", "/home/username/project")
        PosixPath('/absolute/path.txt')
    """
    return LazyPath(path).client_resolve(relative_to=Path(client_cwd))
