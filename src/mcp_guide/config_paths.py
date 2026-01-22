"""Configuration path helpers with test injection support."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


# Private module variables for config overrides
__config_dir: Optional[str] = None
__docroot: Optional[str] = None


def _reset_overrides() -> None:
    """Reset configuration overrides. For testing only."""
    global __config_dir, __docroot
    __config_dir = None
    __docroot = None


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
        return Path.home() / ".config" / "mcp-guide"

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


def get_docroot(config_dir: Optional[str] = None) -> Path:
    """Get document root directory.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to docs directory
    """
    if __docroot:
        return Path(__docroot)

    return get_config_file(config_dir).parent / "docs"
