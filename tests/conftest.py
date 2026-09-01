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
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

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


@pytest.fixture(scope="session", autouse=True)
def disable_default_profile():
    """Disable default profile application for all tests by default."""
    import mcp_guide.session

    original = mcp_guide.session._enable_default_profile
    mcp_guide.session._enable_default_profile = False
    yield
    mcp_guide.session._enable_default_profile = original


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


REPO_ROOT = Path(__file__).resolve().parent.parent


def is_gitignored(repo_root: Path, path: Path) -> bool:
    """Return True when git would ignore this path in the worktree."""
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True
    if relative.parts and relative.parts[0] == ".git":
        return True
    result = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "-q", "--", str(relative)],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


class ProductionFileHandler(FileSystemEventHandler):
    """Abort tests on an identifiable production file event."""

    def __init__(self) -> None:
        super().__init__()
        self._snapshots: dict[Path, dict[Path, tuple[int, int]]] = {}
        self._recursive_paths: set[Path] = set()

    def watch_path(self, path: Path, *, recursive: bool = True) -> None:
        """Record the protected path state before watchdog starts observing it."""
        root = path.resolve()
        if recursive:
            self._recursive_paths.add(root)
        self._snapshots[root] = self._snapshot(root)

    def _snapshot(self, root: Path) -> dict[Path, tuple[int, int]]:
        """Return persistent non-lock file state beneath one protected root."""
        paths = root.rglob("*") if root in self._recursive_paths else root.iterdir()
        snapshot: dict[Path, tuple[int, int]] = {}
        try:
            for path in paths:
                if not path.is_file() or path.name.endswith(".lock"):
                    continue
                try:
                    stat = path.stat()
                except FileNotFoundError:
                    continue
                snapshot[path.resolve()] = (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            return {}
        return snapshot

    def _directory_changes(self, directory: Path) -> list[str]:
        """Identify persistent protected-file changes behind a directory event."""
        changes: list[str] = []
        for root, previous in self._snapshots.items():
            try:
                directory.resolve().relative_to(root)
            except ValueError:
                try:
                    root.relative_to(directory.resolve())
                except ValueError:
                    continue
            current = self._snapshot(root)
            self._snapshots[root] = current
            for path in sorted(current.keys() - previous.keys()):
                changes.append(f"created: {path}")
            for path in sorted(previous.keys() - current.keys()):
                changes.append(f"removed: {path}")
            for path in sorted(current.keys() & previous.keys()):
                if current[path] != previous[path]:
                    changes.append(f"modified: {path}")
        return changes

    def on_any_event(self, event):
        """Abort only when watchdog identifies the affected production file."""
        if getattr(event, "is_directory", False):
            changes = self._directory_changes(Path(event.src_path))
            if changes:
                self._abort(event, changes)
            return

        source_path = event.src_path
        destination_path = getattr(event, "dest_path", "")
        # Ignore transient lock files created by running mcp-guide server instances.
        if source_path.endswith(".lock") or destination_path.endswith(".lock"):
            return

        self._abort(event)

    @staticmethod
    def _abort(event, changes: list[str] | None = None) -> None:
        """Emit a complete, prominent diagnostic before terminating pytest."""
        source_path = event.src_path
        destination_path = getattr(event, "dest_path", "")
        event_class = getattr(event, "event_class", type(event).__name__)
        changed_paths = ""
        if changes:
            changed_paths = "\nDetected file changes:\n" + "\n".join(f"  {change}" for change in changes)
        pytest.exit(
            "!!! PRODUCTION FILE WRITE DETECTED — TEST RUN ABORTED !!!\n"
            f"Event class: {event_class}\n"
            f"Change: {event.event_type}\n"
            f"Path: {source_path}\n"
            f"Destination: {destination_path or '<none>'}\n"
            f"{changed_paths}\n"
            "Tests must use temporary directories for file operations.",
            returncode=1,
        )


class WorktreeFileHandler(FileSystemEventHandler):
    """Terminate tests that modify non-gitignored worktree paths."""

    def __init__(self, repo_root: Path) -> None:
        super().__init__()
        self._repo_root = repo_root.resolve()

    def on_any_event(self, event):
        """Terminate the test session if a tracked worktree file is touched."""
        if getattr(event, "is_directory", False):
            return
        if event.src_path.endswith(".lock"):
            return
        paths = [Path(event.src_path)]
        dest_path = getattr(event, "dest_path", None)
        if dest_path:
            paths.append(Path(dest_path))
        for path in paths:
            if path.resolve() == self._repo_root:
                continue
            if is_gitignored(self._repo_root, path):
                continue
            pytest.exit(
                f"WORKTREE FILE MODIFIED: {path}\n"
                f"Event type: {event.event_type}\n"
                f"Tests must not write non-gitignored files in the repository.",
                returncode=1,
            )


def _create_test_observer():
    """Create a watchdog observer suitable for the current test platform."""
    # Polling is sufficient for this safety-tripwire fixture and avoids the
    # FSEvents teardown crash seen on macOS with Python 3.14.
    if sys.platform == "darwin":
        return PollingObserver(timeout=0.2)
    return Observer()


@pytest.fixture(scope="session", autouse=True)
def protect_production_files():
    """Monitor production XDG paths and the worktree; abort on tracked writes.

    Production paths are captured at module import time, before pytest_configure
    redirects environment variables to temporary directories. Worktree events
    after this fixture starts are violations unless git would ignore the path.
    """
    production_handler = ProductionFileHandler()
    worktree_handler = WorktreeFileHandler(REPO_ROOT)
    observer = _create_test_observer()

    if REAL_PATHS["mcp_guide_config"].exists():
        production_handler.watch_path(REAL_PATHS["mcp_guide_config"], recursive=False)
        observer.schedule(production_handler, str(REAL_PATHS["mcp_guide_config"]), recursive=False)

    if REAL_PATHS["mcp_guide_docroot"].exists():
        production_handler.watch_path(REAL_PATHS["mcp_guide_docroot"])
        observer.schedule(production_handler, str(REAL_PATHS["mcp_guide_docroot"]), recursive=True)

    if REAL_PATHS["msg_config"].exists():
        production_handler.watch_path(REAL_PATHS["msg_config"], recursive=False)
        observer.schedule(production_handler, str(REAL_PATHS["msg_config"]), recursive=False)

    if REAL_PATHS["msg_docroot"].exists():
        production_handler.watch_path(REAL_PATHS["msg_docroot"])
        observer.schedule(production_handler, str(REAL_PATHS["msg_docroot"]), recursive=True)

    observer.schedule(worktree_handler, str(REPO_ROOT), recursive=True)
    observer.start()
    yield
    if observer.is_alive():
        observer.stop()
        observer.join(timeout=5)


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

    # Clean up MCP SDK artifacts
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    for artifact in ["API", "Event"]:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            artifact_path.unlink()


def pytest_sessionfinish(session, exitstatus):
    """Close any remaining event loops after test session."""
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_closed():
            loop.close()
    except RuntimeError:
        # No running loop, nothing to close
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
    # pytest-asyncio handles event loop management automatically
    # This fixture is kept for backwards compatibility but does nothing
    yield None


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
        tool_name: Name of the tool to call (without prefix)
        args_model: Optional Pydantic model instance with tool arguments
        **kwargs: Alternative to args_model - keyword arguments to wrap

    Returns:
        Tool call result

    Examples:
        # Using Pydantic model:
        args = GetCurrentProjectArgs(verbose=True)
        result = await call_mcp_tool(client, "get_project", args)

        # Using kwargs:
        result = await call_mcp_tool(client, "collection_add",
                                     name="backend", categories=["api"])
    """
    from mcp_guide.core.tool_decorator import get_tool_prefix

    # Always use the configured prefix
    prefix = get_tool_prefix().rstrip("_")
    prefixed_tool_name = f"{prefix}_{tool_name}" if prefix else tool_name

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

    return await client.call_tool(prefixed_tool_name, arguments, raise_on_error=False)


def assert_tool_registered(tool_names, tool_name):
    """Helper to assert a tool is registered, handling prefix automatically.

    Args:
        tool_names: List of registered tool names from server
        tool_name: Tool name to check (without prefix)
    """
    from mcp_guide.core.tool_decorator import get_tool_prefix

    # Always use the configured prefix
    prefix = get_tool_prefix().rstrip("_")
    prefixed_tool_name = f"{prefix}_{tool_name}" if prefix else tool_name

    assert prefixed_tool_name in tool_names, f"Tool '{prefixed_tool_name}' not found in registered tools: {tool_names}"


@pytest.fixture(scope="function")
def reset_flag_registry():
    """Capture and restore flag validator/scope registries for test isolation.

    Ensures tests that modify global validator/scope registries don't leak
    state into other tests, preventing order-dependent failures.
    """
    from mcp_guide.feature_flags import validators

    # Capture current state
    saved_validators = validators._FLAG_VALIDATORS.copy()
    saved_scopes = validators._FLAG_SCOPES.copy()
    saved_normalisers = validators._FLAG_NORMALISERS.copy()

    yield

    # Restore original state
    validators._FLAG_VALIDATORS.clear()
    validators._FLAG_VALIDATORS.update(saved_validators)
    validators._FLAG_SCOPES.clear()
    validators._FLAG_SCOPES.update(saved_scopes)
    validators._FLAG_NORMALISERS.clear()
    validators._FLAG_NORMALISERS.update(saved_normalisers)


@pytest.fixture(scope="function")
def guide_function(tmp_path, monkeypatch):
    """Import guide function with server initialization.

    Creates a temporary server instance to enable guide function import.
    Use this fixture in any test that needs to call the guide prompt.
    """
    import logging

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_server
    from tests.helpers import create_unbound_test_session

    # Initialize server to set up mcp instance
    config = ServerConfig()
    create_server(config)

    session = create_unbound_test_session(str(tmp_path))

    async def get_test_session(*_args, **_kwargs):
        return session

    monkeypatch.setattr("mcp_guide.session.get_session", get_test_session)

    # Import guide function after server is initialized
    from mcp_guide.prompts.guide_prompt import guide

    yield guide

    # Clean up logging after test
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    # Reset all loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
        logger.setLevel(logging.NOTSET)
    root.setLevel(logging.WARNING)


@pytest.fixture(scope="function", autouse=True)
def reset_session_for_test():
    """Keep the compatibility fixture while Sessions are explicitly owned.

    Runtime-backed and directly constructed Sessions are cleaned up by the
    tests that create them. There is no process-global session state to reset.
    """
    yield
