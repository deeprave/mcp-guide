"""Configuration path helpers with test injection support."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


# Private module variables for config overrides
__config_dir: Optional[str] = None
__docroot: Optional[str] = None


def set_config_dir(config_dir: str) -> None:
    """Set configuration directory override.

    Args:
        config_dir: Configuration directory path
    """
    global __config_dir
    __config_dir = config_dir


def set_docroot(docroot: str) -> None:
    """Set docroot override.

    Args:
        docroot: Docroot directory path
    """
    global __docroot
    __docroot = docroot


def clear_config_overrides() -> None:
    """Clear process-level config and docroot overrides.

    Tests that start a server or runtime apply these overrides for isolation.
    They must not leak into later tests that read XDG-backed defaults.
    """
    global __config_dir, __docroot
    __config_dir = None
    __docroot = None


def get_config_dir(config_dir: Optional[str] = None) -> Path:
    """Get configuration directory.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to config directory
    """
    if config_dir:
        return Path(config_dir)

    if __config_dir:
        return Path(__config_dir)

    # Unix: XDG_CONFIG_HOME or ~/.config
    if os.name != "nt":
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "mcp-guide"
        return Path("~") / ".config" / "mcp-guide"

    # Windows: APPDATA
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "mcp-guide"
    return Path.home() / "AppData" / "Roaming" / "mcp-guide"


def get_config_file(config_dir: Optional[str] = None) -> Path:
    """Get configuration file path.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to config.yaml file
    """
    return get_config_dir(config_dir) / "config.yaml"


def get_cache_dir() -> Path:
    """Return Guide's user-writable cache directory.

    Unix follows ``XDG_CACHE_HOME`` and defaults to ``~/.cache``.  Windows
    keeps transient application data below the local application-data root.
    """
    if os.name != "nt":
        cache_home = os.environ.get("XDG_CACHE_HOME")
        if cache_home:
            return Path(cache_home) / "mcp-guide"
        return Path("~") / ".cache" / "mcp-guide"

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "mcp-guide" / "cache"
    return Path.home() / "AppData" / "Local" / "mcp-guide" / "cache"


def get_docroot(config_dir: Optional[str] = None) -> Path:
    """Get document root directory.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to docs directory
    """
    # Deferred to avoid the LazyPath/configuration import cycle during startup.
    from mcp_guide.lazy_path import LazyPath

    if __docroot:
        return LazyPath(__docroot).resolve()

    return LazyPath(get_config_file(config_dir).parent / "docs").resolve()


def get_documents_db(config_dir: Optional[str] = None) -> Path:
    """Get document store database path.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to documents.db file
    """
    return get_config_dir(config_dir) / "documents.db"
