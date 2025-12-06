"""Shared fixtures for unit tests."""

import hashlib
import sys
import uuid
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="module", autouse=True)
def reset_tools_proxy_module():
    """Reset tools proxy and reload modules for each test module.

    Ensures unit tests get unwrapped tool functions by resetting the proxy
    and reloading modules before each test module runs.
    """
    from importlib import reload

    from mcp_guide.server import _ToolsProxy

    # Reset proxy to None so tool decorators become no-ops
    _ToolsProxy._instance = None

    # Reload tool modules to re-execute decorators with None proxy
    if "mcp_guide.tools.tool_category" in sys.modules:
        reload(sys.modules["mcp_guide.tools.tool_category"])
    if "mcp_guide.tools.tool_collection" in sys.modules:
        reload(sys.modules["mcp_guide.tools.tool_collection"])
    if "mcp_guide.tools.tool_content" in sys.modules:
        reload(sys.modules["mcp_guide.tools.tool_content"])

    yield

    # Clean up after module
    _ToolsProxy._instance = None


@pytest.fixture
def temp_project_dir(session_temp_dir: Path) -> Generator[Path, None, None]:
    """Provide temporary project directory for tests."""
    # Create subdirectory within session temp dir
    project_subdir = session_temp_dir / f"project_{uuid.uuid4().hex[:8]}"
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
def project_dir(tmp_path: Path, monkeypatch) -> Generator[Path, None, None]:
    """Set up isolated project directory with PWD and CWD.

    Creates a project directory named "test" and sets environment variables
    so that _determine_project_name() will correctly identify the project.

    Args:
        tmp_path: pytest's tmp_path fixture
        monkeypatch: pytest's monkeypatch fixture for isolated env var changes

    Yields:
        Path to the project directory

    Note:
        - Project name will be "test" (derived from directory name)
        - PWD and CWD are set to the project directory
        - Session is automatically cleaned up after test
    """
    from mcp_guide.session import remove_current_session

    project_name = "test"
    test_project_dir = tmp_path / project_name
    test_project_dir.mkdir(exist_ok=True)

    monkeypatch.setenv("PWD", str(test_project_dir))
    monkeypatch.setenv("CWD", str(test_project_dir))

    yield test_project_dir

    remove_current_session(project_name)
