"""Guide-specific MCP server implementation."""

try:
    from importlib.metadata import version

    __version__ = version("mcp-guide")
except Exception:
    # Fallback: read from pyproject.toml during development
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            __version__ = tomllib.load(f)["project"]["version"]
    else:
        __version__ = "unknown"
