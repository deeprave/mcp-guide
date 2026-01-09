"""Project hash utilities for unique project identification."""

import hashlib
from pathlib import Path
from typing import Optional


def calculate_project_hash(path: str) -> str:
    """Calculate SHA256 hash of project path for unique identification.

    SHA256 provides cryptographic-strength collision resistance. The probability
    of two different paths producing the same hash is negligible (2^-256).
    The 8-character short hash used in keys has ~4.3 billion possible values,
    which is sufficient for practical project disambiguation.

    Args:
        path: Full project path (absolute)

    Returns:
        SHA256 hash as hexadecimal string
    """
    # Normalize path to ensure consistent hashing
    normalized_path = str(Path(path).resolve())
    return hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()


async def verify_project_hash(project_hash: Optional[str], current_path: Optional[str] = None) -> bool:
    """Verify if a stored project hash matches the current project path.

    Args:
        project_hash: Stored hash to verify
        current_path: Current path (if None, will be resolved)

    Returns:
        True if hash matches, False otherwise
    """
    if not project_hash:
        return False

    try:
        if current_path is None:
            from mcp_guide.mcp_context import resolve_project_path

            resolved_path = await resolve_project_path()
            current_path = str(resolved_path)

        current_hash = calculate_project_hash(current_path)
        return project_hash == current_hash

    except ValueError:
        # Cannot verify - assume mismatch
        return False


def generate_project_key(name: str, hash_value: str) -> str:
    """Generate project configuration key from name and hash.

    Args:
        name: Project display name
        hash_value: Full SHA256 hash

    Returns:
        Key in format: {name}-{short_hash}
    """
    short_hash = hash_value[:8]
    return f"{name}-{short_hash}"


def extract_name_from_key(key: str) -> str:
    """Extract display name from hash-suffixed project key.

    Args:
        key: Project key in format {name}-{short_hash}

    Returns:
        Project display name
    """
    # Handle both legacy (no hash) and new (with hash) formats
    if "-" in key:
        last_segment = key.split("-")[-1]
        # Check if last segment is exactly 8 hex characters (hash format)
        if len(last_segment) == 8 and all(c in "0123456789abcdef" for c in last_segment.lower()):
            # New format: remove 8-character hash suffix
            return key[:-9]  # Remove "-{8chars}"

    # Legacy format or non-hex last segment: return as-is
    return key
