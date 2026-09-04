"""Lazy path resolution with support for ~ and environment variables."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from anyio import Path as AsyncPath


class LazyPath:
    """Path that resolves lazily when accessed, supporting ~ and ${VAR} expansion."""

    def __init__(self, path: Union[str, Path]):
        """Create a LazyPath from string or Path.

        Args:
            path: Path as string or Path object
        """
        self.path_str = str(path)
        self._resolved_path: Optional[Path] = None

    def expanduser(self) -> str:
        """Expand ~ and ~user constructions.

        Returns:
            Path string with ~ expanded
        """
        return str(Path(self.path_str).expanduser())

    def expandvars(self) -> str:
        """Expand environment variables of form $var and ${var}.

        Returns:
            Path string with environment variables expanded
        """
        return os.path.expandvars(self.path_str)

    def expand(self) -> Path:
        """Expand ~ and environment variables without resolving the filesystem path."""
        return Path(os.path.expandvars(self.path_str)).expanduser()

    def resolve(self, *, strict: bool = False, expand: bool = True) -> Path:
        """Resolve the path.

        Args:
            strict: If True, raise FileNotFoundError if the path doesn't exist
            expand: If True, expand ~ and environment variables before resolving

        Returns:
            Resolved Path object

        Raises:
            OSError: If the path cannot be resolved
            ValueError: If the path string is malformed
            FileNotFoundError: If strict=True and the path doesn't exist
        """
        if self._resolved_path is not None:
            return self._resolved_path

        try:
            path_str = str(self.expand()) if expand else self.path_str
            self._resolved_path = Path(path_str).resolve(strict=strict)
        except FileNotFoundError:
            raise
        except (OSError, ValueError, RuntimeError) as e:
            raise OSError(f"Failed to resolve path '{self.path_str}': {e}") from e

        return self._resolved_path

    async def aresolve(self, *, strict: bool = False, expand: bool = True) -> "AsyncPath":
        """Resolve the path and return an anyio path for async IO.

        Uses the same expandvars, expanduser, and resolve rule as ``resolve()``.
        """
        from anyio import Path as AsyncPath

        if self._resolved_path is not None and not strict:
            return AsyncPath(self._resolved_path)

        try:
            path_str = str(self.expand()) if expand else self.path_str
            resolved = await AsyncPath(path_str).resolve(strict=strict)
        except FileNotFoundError:
            raise
        except (OSError, ValueError, RuntimeError) as e:
            raise OSError(f"Failed to resolve path '{self.path_str}': {e}") from e

        self._resolved_path = Path(resolved)
        return resolved

    def is_absolute(self) -> bool:
        """Check if path is absolute, accounting for ~ and ${VAR} expansions.

        Returns:
            True if the path is absolute after variable expansion
        """
        return self.expand().is_absolute()

    def __str__(self) -> str:
        return self.path_str

    def __repr__(self) -> str:
        return f"LazyPath('{self.path_str}')"
