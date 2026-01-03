"""Configuration path helpers with test injection support."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


def get_config_dir(config_dir: Optional[str] = None) -> Path:
    """Get configuration directory.

    Args:
        config_dir: Optional override directory for testing

    Returns:
        Path to config directory
    """
    if config_dir:
        return Path(config_dir)

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
    return get_config_file(config_dir).parent / "docs"
