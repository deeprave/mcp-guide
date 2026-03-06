"""Tests for permission management tools."""

import pytest

from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_project import (
    AddPermissionPathArgs,
    RemovePermissionPathArgs,
    internal_add_permission_path,
    internal_remove_permission_path,
)


@pytest.fixture
async def test_session(tmp_path):
    """Create a test session with a project."""
    session = Session("test-project", _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)
    yield session
    await remove_current_session("test-project")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permission_type,path,expected_success",
    [
        # Valid write paths
        ("write", "docs/", True),
        ("write", "src/", True),
        ("write", "tests/", True),
        # Valid read paths
        ("read", "/absolute/path", True),
        ("read", "/home/user/data", True),
        # Invalid write paths
        ("write", "/absolute/path", False),  # Must be relative
        ("write", "no-slash", False),  # Must end with /
        # Invalid read paths
        ("read", "relative/path", False),  # Must be absolute
        # Invalid permission type
        ("invalid", "path/", False),
    ],
)
async def test_add_permission_path(permission_type, path, expected_success, test_session):
    """Test adding permission paths with various inputs."""
    args = AddPermissionPathArgs(permission_type=permission_type, path=path)
    result = await internal_add_permission_path(args, None)

    if expected_success:
        assert result.success, f"Expected success for {permission_type}:{path}, got: {result.error}"
    else:
        assert not result.success, f"Expected failure for {permission_type}:{path}"


@pytest.mark.asyncio
async def test_add_permission_path_duplicate(test_session):
    """Test adding duplicate path succeeds silently."""
    # Add path first time
    args = AddPermissionPathArgs(permission_type="write", path="docs/")
    result1 = await internal_add_permission_path(args, None)
    assert result1.success

    # Add same path again - should succeed silently
    result2 = await internal_add_permission_path(args, None)
    assert result2.success
    assert "already" in result2.value.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permission_type,path",
    [
        ("write", "docs/"),
        ("write", "nonexistent/"),
        ("read", "/absolute/path"),
        ("read", "/nonexistent/path"),
    ],
)
async def test_remove_permission_path(permission_type, path, test_session):
    """Test removing permission paths (existing and non-existing)."""
    # Add path first if it's a valid one
    if permission_type == "write" and path == "docs/":
        add_args = AddPermissionPathArgs(permission_type=permission_type, path=path)
        await internal_add_permission_path(add_args, None)

    # Remove path - should always succeed
    remove_args = RemovePermissionPathArgs(permission_type=permission_type, path=path)
    result = await internal_remove_permission_path(remove_args, None)
    assert result.success


@pytest.mark.asyncio
async def test_remove_permission_path_invalid_type(test_session):
    """Test removing path with invalid permission type."""
    args = RemovePermissionPathArgs(permission_type="invalid", path="path/")
    result = await internal_remove_permission_path(args, None)
    assert not result.success
    assert "INVALID_PERMISSION_TYPE" in result.error
