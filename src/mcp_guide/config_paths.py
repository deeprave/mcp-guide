"""Default configuration paths with XDG compliance and Windows support."""

import os
import platform
from pathlib import Path


def get_default_config_file() -> Path:
    """Get default config file path with XDG support on Unix and APPDATA on Windows."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            config_dir = Path(appdata)
        else:
            config_dir = Path.home() / "AppData" / "Roaming"
    else:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home)
        else:
            config_dir = Path.home() / ".config"

    return config_dir / "mcp-guide" / "config.json"


def get_default_docroot() -> Path:
    """Get default docroot path."""
    return get_default_config_file().parent / "docs"
