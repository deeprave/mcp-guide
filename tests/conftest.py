"""Test configuration and fixtures for proper isolation.

This module provides comprehensive test isolation through multiple mechanisms:

1. **Environment Variable Isolation** (pytest_configure hook):
   - Redirects XDG_CONFIG_HOME and XDG_DATA_HOME to temporary directories
   - Ensures all file operations use test-isolated paths
   - Runs BEFORE test collection to catch import-time path caching

2. **Production File Protection** (protect_production_files fixture):
   - Monitors production config and docroot paths with watchdog
   - Terminates tests immediately if production files are modified
   - Protects both mcp-guide and mcp-server-guide paths
   - Only monitors paths that exist (handles gradual migration)

3. **Helper Fixtures**:
   - isolated_config_file: Test-specific config file path
   - temp_project_dir: Unique temporary directory per test
   - unique_category_name: Collision-free category names
   - session_temp_dir: Access to session-wide temp directory
   - event_loop: Session-scoped async event loop

Protected Paths (if they exist):
- mcp-guide config: $XDG_CONFIG_HOME/mcp-guide/
- mcp-guide docroot: $XDG_CONFIG_HOME/mcp-guide/docs/
- mcp-server-guide config: $XDG_CONFIG_HOME/mcp-server-guide/
- mcp-server-guide docroot: $XDG_CONFIG_HOME/mcp-server-guide/docs/
"""

import asyncio
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Export real path constants for test validation
__all__ = [
    "_REAL_HOME",
    "_REAL_MCP_GUIDE_CONFIG",
    "_REAL_MCP_GUIDE_DOCROOT",
    "_REAL_MSG_CONFIG",
    "_REAL_MSG_DOCROOT",
]

# Global session temp directory
_session_temp_dir: Path | None = None

# Capture REAL production paths BEFORE pytest_configure modifies environment
# These are the actual user paths that must be protected
_REAL_HOME = Path.home()
_REAL_XDG_CONFIG = os.environ.get("XDG_CONFIG_HOME", str(_REAL_HOME / ".config"))

# Unix/Linux/macOS paths
_REAL_MCP_GUIDE_CONFIG = Path(_REAL_XDG_CONFIG) / "mcp-guide"
_REAL_MCP_GUIDE_DOCROOT = _REAL_MCP_GUIDE_CONFIG / "docs"
_REAL_MSG_CONFIG = Path(_REAL_XDG_CONFIG) / "mcp-server-guide"
_REAL_MSG_DOCROOT = _REAL_MSG_CONFIG / "docs"

# Windows support for real paths
if os.name == "nt":
    _REAL_APPDATA = os.environ.get("APPDATA", str(_REAL_HOME / "AppData" / "Roaming"))
    _REAL_MCP_GUIDE_CONFIG = Path(_REAL_APPDATA) / "mcp-guide"
    _REAL_MCP_GUIDE_DOCROOT = _REAL_MCP_GUIDE_CONFIG / "docs"
    _REAL_MSG_CONFIG = Path(_REAL_APPDATA) / "mcp-server-guide"
    _REAL_MSG_DOCROOT = _REAL_MSG_CONFIG / "docs"


class ProductionFileHandler(FileSystemEventHandler):
    """Handler that terminates tests immediately on production file modification."""

    def on_any_event(self, event):
        """Terminate test session if production file is touched."""
        pytest.exit(
            f"PRODUCTION FILE MODIFIED: {event.src_path}\n"
            f"Event type: {event.event_type}\n"
            f"Tests must use temporary directories for file operations.",
            returncode=1,
        )


@pytest.fixture(scope="session", autouse=True)
def protect_production_files():
    """Monitor REAL production paths and terminate tests if modified.

    Uses paths captured at module import time, before pytest_configure
    redirects environment variables to temporary directories.
    """
    handler = ProductionFileHandler()
    observer = Observer()

    # Monitor REAL production paths (captured before env modification)
    if _REAL_MCP_GUIDE_CONFIG.exists():
        observer.schedule(handler, str(_REAL_MCP_GUIDE_CONFIG), recursive=False)

    if _REAL_MCP_GUIDE_DOCROOT.exists():
        observer.schedule(handler, str(_REAL_MCP_GUIDE_DOCROOT), recursive=True)

    if _REAL_MSG_CONFIG.exists():
        observer.schedule(handler, str(_REAL_MSG_CONFIG), recursive=False)

    if _REAL_MSG_DOCROOT.exists():
        observer.schedule(handler, str(_REAL_MSG_DOCROOT), recursive=True)

    observer.start()
    yield
    observer.stop()
    observer.join()


def pytest_configure(config):
    """Configure pytest - runs BEFORE any test collection or imports.

    This is the ONLY way to ensure environment variables are set before
    any code imports and caches paths.
    """
    global _session_temp_dir

    # Create session-wide temp directory
    _session_temp_dir = Path(tempfile.mkdtemp(prefix="mcp_test_session_"))

    # Create isolated config and docs directories
    test_config_dir = _session_temp_dir / "config"
    test_docs_dir = _session_temp_dir / "docs"
    test_config_dir.mkdir(parents=True)
    test_docs_dir.mkdir(parents=True)

    # Create mcp-guide subdirectory for config files
    (test_config_dir / "mcp-guide").mkdir(parents=True, exist_ok=True)

    # Override environment variables BEFORE any imports
    os.environ["HOME"] = str(_session_temp_dir)
    os.environ["XDG_CONFIG_HOME"] = str(test_config_dir)
    os.environ["XDG_DATA_HOME"] = str(test_docs_dir)

    # Windows support
    if os.name == "nt":
        os.environ["APPDATA"] = str(test_config_dir)
        os.environ["LOCALAPPDATA"] = str(test_config_dir)


def pytest_unconfigure(config):
    """Cleanup after all tests complete."""
    global _session_temp_dir

    if _session_temp_dir:
        robust_cleanup(_session_temp_dir)
        _session_temp_dir = None


def robust_cleanup(directory: Path) -> None:
    """Robustly clean up a directory, handling read-only files and other issues."""

    def handle_remove_readonly(func, path, _exc):
        """Error handler for shutil.rmtree to handle read-only files."""
        import stat

        if os.path.exists(path):
            # Make the file writable and try again
            os.chmod(path, stat.S_IWRITE)
            func(path)

    if directory.exists():
        shutil.rmtree(directory, onerror=handle_remove_readonly)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def isolated_config_file():
    """Provide an isolated config file path for tests that need real file I/O."""
    from mcp_guide.config_paths import get_default_config_file

    config_path = get_default_config_file()

    if config_path.exists():
        config_path.unlink()

    yield config_path

    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Provide temporary project directory for tests."""
    import uuid

    global _session_temp_dir

    assert _session_temp_dir is not None, "Session temp dir not initialized by pytest_configure"

    # Create subdirectory within session temp dir
    project_subdir = _session_temp_dir / f"project_{uuid.uuid4().hex[:8]}"
    project_subdir.mkdir(parents=True, exist_ok=True)

    yield project_subdir


@pytest.fixture
def unique_category_name(request):
    """Generate a unique category name for each test to prevent conflicts.

    Category names must be alphanumeric with hyphens/underscores and max 30 chars.
    """
    # Use hash of test node ID to create short unique name
    test_id = request.node.nodeid
    hash_val = hashlib.md5(test_id.encode()).hexdigest()[:8]
    return f"cat_{hash_val}"


@pytest.fixture
def session_temp_dir() -> Path:
    """Provide access to session temp directory."""
    global _session_temp_dir
    assert _session_temp_dir is not None, "Session temp dir not initialized by pytest_configure"
    return _session_temp_dir
