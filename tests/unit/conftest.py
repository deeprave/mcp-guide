"""Shared fixtures for unit tests."""

import hashlib
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest


@pytest.fixture
def task_manager():
    """Create a fresh TaskManager for each test."""
    from mcp_guide.task_manager.manager import TaskManager

    return TaskManager()


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
async def project_dir(tmp_path: Path, monkeypatch) -> AsyncGenerator[Path, None]:
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
    project_name = "test"
    test_project_dir = tmp_path / project_name
    test_project_dir.mkdir(exist_ok=True)

    monkeypatch.setenv("PWD", str(test_project_dir))
    monkeypatch.setenv("CWD", str(test_project_dir))

    yield test_project_dir
