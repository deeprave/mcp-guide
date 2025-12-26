"""Template partial utilities for path resolution and content loading."""

from pathlib import Path
from typing import List


class PartialNotFoundError(Exception):
    """Raised when a partial template file cannot be found."""

    pass


def resolve_partial_paths(template_path: Path, includes: List[str], docroot: Path | None = None) -> List[Path]:
    """Resolve partial paths relative to template file.

    Args:
        template_path: Path to the template file
        includes: List of partial paths to resolve
        docroot: Root directory for security validation (defaults to current working directory)

    Returns:
        List of resolved absolute paths to partial files

    Raises:
        PartialNotFoundError: If partial path is outside docroot or invalid
    """
    template_dir = template_path.parent
    if docroot is None:
        docroot = Path.cwd()
    docroot = docroot.resolve()
    resolved_paths = []

    for include in includes:
        # Reject absolute paths
        if include.startswith("/"):
            raise PartialNotFoundError(f"Absolute paths not allowed: {include}")

        # Resolve path relative to template directory
        partial_path = (template_dir / include).resolve()

        # Ensure resolved path is within docroot
        try:
            partial_path.relative_to(docroot)
        except ValueError:
            raise PartialNotFoundError(f"Partial path outside docroot: {include}")

        resolved_paths.append(partial_path)

    return resolved_paths


def load_partial_content(partial_path: Path) -> str:
    """Load content from a partial template file.

    Args:
        partial_path: Path to the partial file

    Returns:
        Content of the partial file

    Raises:
        PartialNotFoundError: If the partial file does not exist
    """
    if not partial_path.exists():
        raise PartialNotFoundError(f"Partial template not found: {partial_path}")

    return partial_path.read_text(encoding="utf-8")
