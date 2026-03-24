"""URI parser for guide:// scheme."""

from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class GuideUri:
    """Parsed guide:// URI."""

    is_command: bool
    expression: str
    pattern: str | None = None
    args: list[str] = field(default_factory=list)
    kwargs: dict[str, str | bool] = field(default_factory=dict)


def _parse_query_kwargs(query: str) -> dict[str, str | bool]:
    """Parse query string into kwargs with boolean inference."""
    if not query:
        return {}
    kwargs: dict[str, str | bool] = {}
    for key, values in parse_qs(query, keep_blank_values=True).items():
        value = values[0] if values else ""
        match value.lower():
            case "" | "true":
                kwargs[key] = True
            case "false":
                kwargs[key] = False
            case _:
                kwargs[key] = value
    return kwargs


def _resolve_command(path_segments: list[str], command_names: list[str]) -> tuple[str, list[str]]:
    """Resolve longest matching command path, return (command_path, remaining_args)."""
    for i in range(len(path_segments), 0, -1):
        candidate = "/".join(path_segments[:i])
        if candidate in command_names:
            return candidate, path_segments[i:]
    # No match — use first segment as command, rest as args
    return path_segments[0], path_segments[1:]


def parse_guide_uri(uri: str, command_names: list[str] | None = None) -> GuideUri:
    """Parse a guide:// URI into its components.

    Args:
        uri: Full guide:// URI string
        command_names: Known command names for longest-match resolution

    Returns:
        Parsed GuideUri

    Raises:
        ValueError: If URI scheme is not guide://
    """
    parsed = urlparse(uri)
    if parsed.scheme != "guide":
        raise ValueError(f"Only guide:// URIs are supported, got: {parsed.scheme}://")

    # Reconstruct full path from netloc + path
    full_path = parsed.netloc
    if parsed.path and parsed.path != "/":
        full_path += parsed.path

    if not full_path:
        raise ValueError("Empty guide:// URI")

    # Command URI: underscore prefix
    if full_path.startswith("_"):
        segments = [s for s in full_path[1:].split("/") if s]
        if not segments:
            raise ValueError("Empty command path in guide:// URI")
        command_path, args = _resolve_command(segments, command_names or [])
        kwargs = _parse_query_kwargs(parsed.query)
        return GuideUri(is_command=True, expression=command_path, args=args, kwargs=kwargs)

    # Content URI: expression[/pattern]
    parts = full_path.split("/", 1)
    expression = parts[0]
    pattern = parts[1] if len(parts) > 1 and parts[1] else None
    return GuideUri(is_command=False, expression=expression, pattern=pattern)
