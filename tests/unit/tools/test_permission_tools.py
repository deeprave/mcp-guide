"""Tests for permission management tools."""

import pytest
from tests.helpers import create_test_session

from mcp_guide.session import remove_current_session, set_current_session
from mcp_guide.tools.tool_project import (
    AddPermissionPathArgs,
    RemovePermissionPathArgs,
    internal_add_permission_path,
    internal_remove_permission_path,
)


@pytest.fixture
async def test_session(tmp_path):
    """Create a test session with a project."""
    # Use a unique project name per test to avoid state pollution
    import uuid

    project_name = f"test-{uuid.uuid4().hex[:8]}"
    session = await create_test_session(project_name, _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)
    yield session
    await remove_current_session()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "permission_type,path,expected_success",
    [
        # Valid write paths - directories
        ("write", "docs/", True),
        ("write", "src/", True),
        ("write", "tests/", True),
        # Valid write paths - specific files
        ("write", "config.json", True),
        ("write", ".guide.yaml", True),
        # Valid write paths - absolute
        ("write", "/tmp/exports/", True),
        ("write", "/home/user/knowledge/", True),
        # Valid read paths
        ("read", "/absolute/path", True),
        ("read", "/home/user/data", True),
        # Invalid write paths - system directories
        ("write", "/etc/", False),
        ("write", "/sys/kernel/", False),
        # Invalid read paths
        ("read", "relative/path", False),  # Must be absolute
    ],
)
async def test_add_permission_path(permission_type, path, expected_success, test_session):
    """Test adding permission paths with various inputs."""
    args = AddPermissionPathArgs(permission_type=permission_type, path=path)
    result = await internal_add_permission_path(args, None)

    if expected_success:
        assert result.success, f"Expected success for {permission_type}:{path}, got: {result.error}"
        assert "Added" in result.value or "already" in result.value
    else:
        assert not result.success, f"Expected failure for {permission_type}:{path}"


@pytest.mark.anyio
async def test_add_permission_path_rejects_system_directory(monkeypatch, test_session):
    """Test that system directories are rejected for read permissions."""

    # Monkeypatch is_system_directory in the module where it's imported from
    def fake_is_system_directory(path: str) -> bool:
        return path == "/fake/system/dir"

    monkeypatch.setattr("mcp_guide.filesystem.system_directories.is_system_directory", fake_is_system_directory)

    args = AddPermissionPathArgs(permission_type="read", path="/fake/system/dir")
    result = await internal_add_permission_path(args, None)

    assert not result.success
    assert result.error == "INVALID_PATH"
    assert "System directory not allowed" in result.error_type


@pytest.mark.anyio
async def test_add_permission_path_validate_error_mapped_to_invalid_path(test_session):
    """Test that Project validator errors are mapped to INVALID_PATH Result."""
    # Use a path that will trigger validation error (path traversal)
    args = AddPermissionPathArgs(permission_type="write", path="../outside/")
    result = await internal_add_permission_path(args, None)

    assert not result.success
    assert result.error == "INVALID_PATH"
    # The error message comes from the Project validator
    assert "traversal" in result.error_type.lower() or "outside" in result.error_type.lower()


@pytest.mark.anyio
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "permission_type,path",
    [
        ("write", "custom/"),
        ("write", "nonexistent/"),
        ("read", "/absolute/path"),
        ("read", "/nonexistent/path"),
    ],
)
async def test_remove_permission_path(permission_type, path, test_session):
    """Test removing permission paths (existing and non-existing)."""
    # Add path first if it's a valid one
    if (permission_type, path) in [("write", "custom/"), ("read", "/absolute/path")]:
        add_args = AddPermissionPathArgs(permission_type=permission_type, path=path)
        await internal_add_permission_path(add_args, None)

    # Remove path - should always succeed
    remove_args = RemovePermissionPathArgs(permission_type=permission_type, path=path)
    result = await internal_remove_permission_path(remove_args, None)
    assert result.success

    # For paths that were actually added, verify state was updated
    if (permission_type, path) == ("write", "custom/"):
        project = await test_session.get_project()
        assert path not in project.allowed_write_paths, "Path should be removed from write paths"
    elif (permission_type, path) == ("read", "/absolute/path"):
        project = await test_session.get_project()
        assert path not in project.additional_read_paths, "Path should be removed from read paths"


@pytest.mark.anyio
async def test_remove_permission_path_invalid_type(test_session):
    """Test that invalid permission type is rejected at parse time by Literal type."""
    import pytest
    from pydantic_core import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        RemovePermissionPathArgs(permission_type="invalid", path="path/")

    assert "literal_error" in str(exc_info.value)


@pytest.mark.anyio
async def test_write_permission_file_vs_directory(test_session):
    """Test that file and directory write permissions work correctly."""
    from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError

    # Setup: Allow specific file and directory
    policy = ReadWriteSecurityPolicy(write_allowed_paths=["config.json", "docs/"], additional_read_paths=[])

    # File permission: exact match only
    assert policy.validate_write_path("config.json") == "config.json"

    with pytest.raises(SecurityError):
        policy.validate_write_path("config.yaml")  # Different file

    with pytest.raises(SecurityError):
        policy.validate_write_path("config.json.bak")  # Not exact match

    # Directory permission: prefix match
    assert policy.validate_write_path("docs/file.txt") == "docs/file.txt"
    assert policy.validate_write_path("docs/sub/file.txt") == "docs/sub/file.txt"

    with pytest.raises(SecurityError):
        policy.validate_write_path("doc/file.txt")  # Different directory
