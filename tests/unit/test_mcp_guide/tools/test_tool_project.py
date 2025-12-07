"""Unit tests for project management tools."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_core.result import Result
from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_project import (
    GetCurrentProjectArgs,
    SetCurrentProjectArgs,
    get_current_project,
    set_current_project,
)


class TestGetCurrentProject:
    """Tests for get_current_project tool."""

    def test_args_validation(self):
        """Test GetCurrentProjectArgs schema validation."""
        # Test verbose=True
        args = GetCurrentProjectArgs(verbose=True)
        assert args.verbose is True

        # Test verbose=False
        args = GetCurrentProjectArgs(verbose=False)
        assert args.verbose is False

        # Test default value
        args = GetCurrentProjectArgs()
        assert args.verbose is False

    @pytest.mark.asyncio
    async def test_no_context_error(self):
        """Test get_current_project with no project context."""
        # Mock get_or_create_session to raise ValueError
        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=ValueError("Project context not available"),
        ):
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "no_project"
            assert "Project context not available" in result["error"]

    @pytest.mark.asyncio
    async def test_non_verbose_output(self, tmp_path: Path, monkeypatch):
        """Test get_current_project with verbose=False returns names only."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        # Create project with data
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test-project")

        project = Project(
            name="test-project",
            categories=[
                Category(name="python", dir="src/", patterns=["*.py"], description="Python source files"),
                Category(name="typescript", dir="src/", patterns=["*.ts"], description="TypeScript files"),
            ],
            collections=[
                Collection(name="api-docs", description="API documentation", categories=["python", "typescript"])
            ],
        )
        session._cached_project = project
        set_current_session(session)

        try:
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["project"] == "test-project"
            assert result["value"]["collections"] == ["api-docs"]
            assert set(result["value"]["categories"]) == {"python", "typescript"}

            # Ensure collections and categories are lists of strings, not dicts
            assert all(isinstance(c, str) for c in result["value"]["collections"])
            assert all(isinstance(c, str) for c in result["value"]["categories"])
        finally:
            remove_current_session("test-project")

    @pytest.mark.asyncio
    async def test_verbose_output(self, tmp_path: Path, monkeypatch):
        """Test get_current_project with verbose=True returns full details."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        # Create project with data
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test-project")

        project = Project(
            name="test-project",
            categories=[
                Category(name="python", dir="src/", patterns=["*.py"], description="Python source files"),
                Category(name="typescript", dir="src/", patterns=["*.ts"], description="TypeScript files"),
            ],
            collections=[
                Collection(name="api-docs", description="API documentation", categories=["python", "typescript"])
            ],
        )
        session._cached_project = project
        set_current_session(session)

        try:
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await get_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["project"] == "test-project"

            # Check collections are dicts with full details
            assert len(result["value"]["collections"]) == 1
            collection = result["value"]["collections"][0]
            assert collection["name"] == "api-docs"
            assert collection["description"] == "API documentation"
            assert set(collection["categories"]) == {"python", "typescript"}

            # Check categories are dicts with full details
            assert len(result["value"]["categories"]) == 2
            category_names = {c["name"] for c in result["value"]["categories"]}
            assert category_names == {"python", "typescript"}

            for category in result["value"]["categories"]:
                assert "name" in category
                assert "dir" in category
                assert "patterns" in category
                assert "description" in category
                assert isinstance(category["patterns"], list)
        finally:
            remove_current_session("test-project")

    @pytest.mark.asyncio
    async def test_empty_project(self, tmp_path: Path, monkeypatch):
        """Test get_current_project with empty project."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/empty-project")

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="empty-project")
        session._cached_project = Project(name="empty-project", categories=[], collections=[])
        set_current_session(session)

        try:
            # Test non-verbose
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["project"] == "empty-project"
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []

            # Test verbose
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await get_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["project"] == "empty-project"
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []
        finally:
            remove_current_session("empty-project")


class TestSetCurrentProject:
    """Tests for set_current_project tool."""

    def test_args_validation(self):
        """Test SetCurrentProjectArgs schema validation."""
        # Test with name and verbose=True
        args = SetCurrentProjectArgs(name="test-project", verbose=True)
        assert args.name == "test-project"
        assert args.verbose is True

        # Test with name and verbose=False
        args = SetCurrentProjectArgs(name="test-project", verbose=False)
        assert args.name == "test-project"
        assert args.verbose is False

        # Test default verbose value
        args = SetCurrentProjectArgs(name="test-project")
        assert args.name == "test-project"
        assert args.verbose is False

    @pytest.mark.asyncio
    async def test_invalid_project_name(self):
        """Test set_current_project with invalid project name."""
        # Mock set_project to return failure for invalid name
        mock_result = Result.failure(
            "Project name 'invalid@name' must contain only alphanumeric characters, underscores, and hyphens",
            error_type="invalid_name",
        )

        with patch("mcp_guide.tools.tool_project.set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="invalid@name", verbose=False)
            result_str = await set_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "invalid_name"
            assert "must contain only alphanumeric" in result["error"]

    @pytest.mark.asyncio
    async def test_switch_existing_project_non_verbose(self):
        """Test switching to existing project with verbose=False."""
        # Create mock project
        project = Project(
            name="existing-project",
            categories=[
                Category(name="python", dir="src/", patterns=["*.py"], description="Python files"),
                Category(name="docs", dir="docs/", patterns=["*.md"], description="Documentation"),
            ],
            collections=[Collection(name="backend", categories=["python"], description="Backend code")],
        )

        # Mock set_project to return success
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="existing-project", verbose=False)
            result_str = await set_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'existing-project'"
            assert result["value"]["project"] == "existing-project"
            assert result["value"]["collections"] == ["backend"]
            assert result["value"]["categories"] == ["python", "docs"]

    @pytest.mark.asyncio
    async def test_switch_existing_project_verbose(self):
        """Test switching to existing project with verbose=True."""
        # Create mock project
        project = Project(
            name="existing-project",
            categories=[
                Category(name="python", dir="src/", patterns=["*.py"], description="Python files"),
                Category(name="docs", dir="docs/", patterns=["*.md"], description="Documentation"),
            ],
            collections=[Collection(name="backend", categories=["python"], description="Backend code")],
        )

        # Mock set_project to return success
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="existing-project", verbose=True)
            result_str = await set_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'existing-project'"
            assert result["value"]["project"] == "existing-project"

            # Check collections verbose format
            assert len(result["value"]["collections"]) == 1
            assert result["value"]["collections"][0]["name"] == "backend"
            assert result["value"]["collections"][0]["description"] == "Backend code"
            assert result["value"]["collections"][0]["categories"] == ["python"]

            # Check categories verbose format
            assert len(result["value"]["categories"]) == 2
            assert result["value"]["categories"][0]["name"] == "python"
            assert result["value"]["categories"][0]["dir"] == "src/"
            assert result["value"]["categories"][0]["patterns"] == ["*.py"]
            assert result["value"]["categories"][0]["description"] == "Python files"

    @pytest.mark.asyncio
    async def test_create_new_project(self):
        """Test creating new project when it doesn't exist."""
        # Create mock project (simulating newly created)
        project = Project(
            name="new-project",
            categories=[],
            collections=[],
        )

        # Mock set_project to return success (set_project handles creation)
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="new-project", verbose=False)
            result_str = await set_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'new-project'"
            assert result["value"]["project"] == "new-project"
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []

    @pytest.mark.asyncio
    async def test_error_passthrough(self):
        """Test that errors from set_project are passed through."""
        # Mock set_project to return a generic error
        mock_result = Result.failure("Configuration file corrupted", error_type="project_load_error")

        with patch("mcp_guide.tools.tool_project.set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="broken-project", verbose=False)
            result_str = await set_current_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "project_load_error"
            assert "Configuration file corrupted" in result["error"]
