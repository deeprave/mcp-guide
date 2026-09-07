"""Shared fixtures for unit tests."""

import hashlib
import uuid
from pathlib import Path
from typing import Generator

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
