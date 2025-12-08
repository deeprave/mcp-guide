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
   - tmp_path: Test-specific config file path
   - temp_project_dir: Unique temporary directory per test
   - unique_category_name: Collision-free category names
   - session_temp_dir: Access to session-wide temp directory

Protected Paths (if they exist):
- mcp-guide config: $XDG_CONFIG_HOME/mcp-guide/
- mcp-guide docroot: $XDG_CONFIG_HOME/mcp-guide/docs/
- mcp-server-guide config: $XDG_CONFIG_HOME/mcp-server-guide/
- mcp-server-guide docroot: $XDG_CONFIG_HOME/mcp-server-guide/docs/
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Export real path constants for test validation
__all__ = [
    "REAL_PATHS",
]

# Global session temp directory
_session_temp_dir: Path | None = None

# Capture REAL production paths BEFORE pytest_configure modifies environment
# These are the actual user paths that must be protected
_REAL_HOME = Path.home()
_REAL_XDG_CONFIG = os.environ.get("XDG_CONFIG_HOME", str(_REAL_HOME / ".config"))

# Store real paths in a dictionary for easy access
REAL_PATHS = {
    "home": _REAL_HOME,
    "xdg_config": Path(_REAL_XDG_CONFIG),
    "mcp_guide_config": Path(_REAL_XDG_CONFIG) / "mcp-guide",
    "mcp_guide_docroot": Path(_REAL_XDG_CONFIG) / "mcp-guide" / "docs",
    "msg_config": Path(_REAL_XDG_CONFIG) / "mcp-server-guide",
    "msg_docroot": Path(_REAL_XDG_CONFIG) / "mcp-server-guide" / "docs",
}

# Windows support for real paths
if os.name == "nt":
    _REAL_APPDATA = os.environ.get("APPDATA", str(_REAL_HOME / "AppData" / "Roaming"))
    REAL_PATHS.update(
        {
            "mcp_guide_config": Path(_REAL_APPDATA) / "mcp-guide",
            "mcp_guide_docroot": Path(_REAL_APPDATA) / "mcp-guide" / "docs",
            "msg_config": Path(_REAL_APPDATA) / "mcp-server-guide",
            "msg_docroot": Path(_REAL_APPDATA) / "mcp-server-guide" / "docs",
        }
    )


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
    if REAL_PATHS["mcp_guide_config"].exists():
        observer.schedule(handler, str(REAL_PATHS["mcp_guide_config"]), recursive=False)

    if REAL_PATHS["mcp_guide_docroot"].exists():
        observer.schedule(handler, str(REAL_PATHS["mcp_guide_docroot"]), recursive=True)

    if REAL_PATHS["msg_config"].exists():
        observer.schedule(handler, str(REAL_PATHS["msg_config"]), recursive=False)

    if REAL_PATHS["msg_docroot"].exists():
        observer.schedule(handler, str(REAL_PATHS["msg_docroot"]), recursive=True)

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


def pytest_sessionfinish(session, exitstatus):
    """Close any remaining event loops after test session."""
    # Get all event loops and close them
    try:
        policy = asyncio.get_event_loop_policy()
        if hasattr(policy, "_local") and hasattr(policy._local, "_loop"):
            loop = policy._local._loop
            if loop and not loop.is_closed():
                loop.close()
    except (RuntimeError, AttributeError):
        # Ignore errors during event loop cleanup; loops may already be closed or missing
        pass


@pytest.fixture(scope="session")
def session_temp_dir() -> Path:
    """Provide access to session temp directory."""
    global _session_temp_dir
    assert _session_temp_dir is not None, "Session temp dir not initialized by pytest_configure"
    return _session_temp_dir


@pytest.fixture(scope="module")
def event_loop_policy():
    """Set event loop policy for the test module."""
    policy = asyncio.get_event_loop_policy()
    yield policy
    # Close any loops created by this module
    try:
        # Use get_event_loop_policy() to avoid deprecation warning
        if hasattr(policy, "_local") and hasattr(policy._local, "_loop"):
            loop = policy._local._loop
            if loop and not loop.is_closed():
                loop.close()
    except (RuntimeError, AttributeError):
        # Ignore errors during event loop cleanup; loops may already be closed or missing
        pass


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


# MCP Tool Call Helper
async def call_mcp_tool(client, tool_name: str, args_model=None, **kwargs):
    """Helper to call MCP tools with proper argument wrapping.

    Args:
        client: MCP client session
        tool_name: Name of the tool to call
        args_model: Optional Pydantic model instance with tool arguments
        **kwargs: Alternative to args_model - keyword arguments to wrap

    Returns:
        Tool call result

    Examples:
        # Using Pydantic model:
        args = GetCurrentProjectArgs(verbose=True)
        result = await call_mcp_tool(client, "get_current_project", args)

        # Using kwargs:
        result = await call_mcp_tool(client, "collection_add",
                                     name="backend", categories=["api"])
    """
    if args_model is not None:
        # Convert Pydantic model to dict and wrap in "args"
        from pydantic import BaseModel

        if isinstance(args_model, BaseModel):
            arguments = {"args": args_model.model_dump()}
        else:
            arguments = {"args": args_model}
    elif kwargs:
        # Wrap kwargs in "args"
        arguments = {"args": kwargs}
    else:
        # No arguments
        arguments = {"args": {}}

    return await client.call_tool(tool_name, arguments)
