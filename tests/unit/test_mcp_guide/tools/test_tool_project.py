"""Unit tests for project management tools."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_core.result import Result
from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_constants import ERROR_SAFEGUARD
from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    GetCurrentProjectArgs,
    ListProjectArgs,
    ListProjectsArgs,
    SetCurrentProjectArgs,
    clone_project,
    get_project,
    list_project,
    list_projects,
    set_project,
)


class TestGetProject:
    """Tests for get_project tool."""

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
        """Test get_project with no project context."""
        # Mock get_or_create_session to raise ValueError
        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=ValueError("Project context not available"),
        ):
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "no_project"
            assert "Project context not available" in result["error"]

    @pytest.mark.asyncio
    async def test_non_verbose_output(self, tmp_path: Path, monkeypatch):
        """Test get_project with verbose=False returns names only."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        # Create project with data
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test-project")

        project = Project(
            name="test-project",
            categories={
                "python": Category(dir="src/", patterns=["*.py"], description="Python source files"),
                "typescript": Category(dir="src/", patterns=["*.ts"], description="TypeScript files"),
            },
            collections={"api-docs": Collection(description="API documentation", categories=["python", "typescript"])},
        )
        session._cached_project = project
        set_current_session(session)

        try:
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["collections"] == ["api-docs"]
            assert set(result["value"]["categories"]) == {"python", "typescript"}

            # Ensure collections and categories are lists of strings, not dicts
            assert all(isinstance(c, str) for c in result["value"]["collections"])
            assert all(isinstance(c, str) for c in result["value"]["categories"])
        finally:
            remove_current_session("test-project")

    @pytest.mark.asyncio
    async def test_verbose_output(self, tmp_path: Path, monkeypatch):
        """Test get_project with verbose=True returns full details."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        # Create project with data
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test-project")

        project = Project(
            name="test-project",
            categories={
                "python": Category(dir="src/", patterns=["*.py"], description="Python source files"),
                "typescript": Category(dir="src/", patterns=["*.ts"], description="TypeScript files"),
            },
            collections={"api-docs": Collection(description="API documentation", categories=["python", "typescript"])},
        )
        session._cached_project = project
        set_current_session(session)

        try:
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is True

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
        """Test get_project with empty project."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/empty-project")

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="empty-project")
        session._cached_project = Project(name="empty-project", categories={}, collections={})
        set_current_session(session)

        try:
            # Test non-verbose
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []

            # Test verbose
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []
        finally:
            remove_current_session("empty-project")


class TestSetProject:
    """Tests for set_project tool."""

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
        """Test set_project with invalid project name."""
        # Mock set_project to return failure for invalid name
        mock_result = Result.failure(
            "Project name 'invalid@name' must contain only alphanumeric characters, underscores, and hyphens",
            error_type="invalid_name",
        )

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="invalid@name", verbose=False)
            result_str = await set_project(args)
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
            categories={
                "python": Category(dir="src/", patterns=["*.py"], description="Python files"),
                "docs": Category(dir="docs/", patterns=["*.md"], description="Documentation"),
            },
            collections={"backend": Collection(categories=["python"], description="Backend code")},
        )

        # Mock set_project to return success
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="existing-project", verbose=False)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'existing-project'"
            assert result["value"]["collections"] == ["backend"]
            assert result["value"]["categories"] == ["python", "docs"]

    @pytest.mark.asyncio
    async def test_switch_existing_project_verbose(self):
        """Test switching to existing project with verbose=True."""
        # Create mock project
        project = Project(
            name="existing-project",
            categories={
                "python": Category(dir="src/", patterns=["*.py"], description="Python files"),
                "docs": Category(dir="docs/", patterns=["*.md"], description="Documentation"),
            },
            collections={"backend": Collection(categories=["python"], description="Backend code")},
        )

        # Mock set_project to return success
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="existing-project", verbose=True)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'existing-project'"

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
            categories={},
            collections={},
        )

        # Mock set_project to return success (set_project handles creation)
        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="new-project", verbose=False)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'new-project'"
            assert result["value"]["collections"] == []
            assert result["value"]["categories"] == []

    @pytest.mark.asyncio
    async def test_error_passthrough(self):
        """Test that errors from set_project are passed through."""
        # Mock set_project to return a generic error
        mock_result = Result.failure("Configuration file corrupted", error_type="project_load_error")

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="broken-project", verbose=False)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "project_load_error"
            assert "Configuration file corrupted" in result["error"]


class TestListProjects:
    """Tests for list_projects tool."""

    def test_args_validation(self):
        """Test ListProjectsArgs schema validation."""
        # Test verbose=True
        args = ListProjectsArgs(verbose=True)
        assert args.verbose is True

        # Test verbose=False
        args = ListProjectsArgs(verbose=False)
        assert args.verbose is False

        # Test default value
        args = ListProjectsArgs()
        assert args.verbose is False

    @pytest.mark.asyncio
    async def test_list_projects_non_verbose(self):
        """Test list_projects returns project names in non-verbose mode."""
        mock_result = Result.ok({"projects": ["alpha", "beta", "gamma"]})

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=False)
            result_str = await list_projects(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["projects"] == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_list_projects_verbose(self):
        """Test list_projects returns full details in verbose mode."""
        mock_result = Result.ok(
            {
                "projects": {
                    "project1": {"categories": [], "collections": []},
                    "project2": {"categories": [], "collections": []},
                }
            }
        )

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=True)
            result_str = await list_projects(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert "project1" in result["value"]["projects"]
            assert "project2" in result["value"]["projects"]

    @pytest.mark.asyncio
    async def test_list_projects_error(self):
        """Test list_projects propagates errors from list_all_projects."""
        mock_result = Result.failure("Failed to read configuration: Permission denied")

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=False)
            result_str = await list_projects(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "Failed to read configuration" in result["error"]


class TestListProject:
    """Tests for list_project tool."""

    def test_args_validation(self):
        """Test ListProjectArgs schema validation."""
        # Test with name
        args = ListProjectArgs(name="test-project", verbose=True)
        assert args.name == "test-project"
        assert args.verbose is True

        # Test defaults
        args = ListProjectArgs()
        assert args.name is None
        assert args.verbose is False

    @pytest.mark.asyncio
    async def test_list_project_current_project(self):
        """Test list_project with no name (defaults to current)."""
        mock_result = Result.ok({"categories": [], "collections": []})

        with patch("mcp_guide.session.get_project_info", new=AsyncMock(return_value=mock_result)):
            args = ListProjectArgs(name=None, verbose=False)
            result_str = await list_project(args)
            result = json.loads(result_str)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_project_specific_project(self):
        """Test list_project with specific project name."""
        mock_result = Result.ok({"categories": [], "collections": []})

        with patch("mcp_guide.session.get_project_info", new=AsyncMock(return_value=mock_result)):
            args = ListProjectArgs(name="other-project", verbose=False)
            result_str = await list_project(args)
            result = json.loads(result_str)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_project_verbose(self):
        """Test list_project with verbose mode."""
        mock_result = Result.ok(
            {
                "categories": [{"name": "docs", "dir": "docs", "patterns": ["*.md"], "description": None}],
                "collections": [{"name": "all", "description": None, "categories": ["docs"]}],
            }
        )

        with patch("mcp_guide.session.get_project_info", new=AsyncMock(return_value=mock_result)):
            args = ListProjectArgs(name="test-project", verbose=True)
            result_str = await list_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert isinstance(result["value"]["categories"], list)
            assert result["value"]["categories"][0]["name"] == "docs"

    @pytest.mark.asyncio
    async def test_list_project_project_not_found(self):
        """Test list_project error propagation."""
        mock_result = Result.failure("Project 'nonexistent' not found", error_type="project_not_found")

        with patch("mcp_guide.session.get_project_info", new=AsyncMock(return_value=mock_result)):
            args = ListProjectArgs(name="nonexistent", verbose=False)
            result_str = await list_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "not found" in result["error"]


def test_error_safeguard_constant():
    """Test ERROR_SAFEGUARD constant exists and has correct value."""
    assert ERROR_SAFEGUARD == "safeguard_prevented"


class TestCloneProjectArgs:
    """Tests for CloneProjectArgs schema."""

    def test_args_validation_all_params(self):
        """Test CloneProjectArgs with all parameters."""
        args = CloneProjectArgs(from_project="source", to_project="target", merge=False, force=True)
        assert args.from_project == "source"
        assert args.to_project == "target"
        assert args.merge is False
        assert args.force is True

    def test_args_default_values(self):
        """Test CloneProjectArgs default values."""
        args = CloneProjectArgs(from_project="source")
        assert args.from_project == "source"
        assert args.to_project is None  # Default
        assert args.merge is True  # Default
        assert args.force is False  # Default

    def test_args_1arg_mode(self):
        """Test CloneProjectArgs for 1-arg mode (to_project=None)."""
        args = CloneProjectArgs(from_project="source", to_project=None)
        assert args.from_project == "source"
        assert args.to_project is None

    def test_args_2arg_mode(self):
        """Test CloneProjectArgs for 2-arg mode (to_project specified)."""
        args = CloneProjectArgs(from_project="source", to_project="target")
        assert args.from_project == "source"
        assert args.to_project == "target"


class TestCloneProject:
    """Tests for clone_project tool."""

    @pytest.mark.asyncio
    async def test_source_project_not_found(self):
        """Test clone_project with non-existent source project."""
        mock_projects = {"existing-project": Project(name="existing-project", categories={}, collections={})}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)

        with patch("mcp_guide.tools.tool_project.get_or_create_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="nonexistent")
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert "not found" in result["error"].lower()
            assert result["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_invalid_source_project_name(self):
        """Test clone_project with invalid source project name."""
        # No mocking needed - validation happens before session access
        args = CloneProjectArgs(from_project="../etc")
        result_str = await clone_project(args)
        result = json.loads(result_str)

        assert result["success"] is False
        assert result["error_type"] == "invalid_name"

    @pytest.mark.asyncio
    async def test_1arg_mode_uses_current_project(self):
        """Test clone_project with to_project=None uses current project."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})
        current_proj = Project(name="current", categories={}, collections={})

        mock_projects = {"source": source_proj, "current": current_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.get_project = AsyncMock(return_value=current_proj)
        mock_session.save_project = AsyncMock()
        mock_session.invalidate_cache = Mock()

        with patch("mcp_guide.tools.tool_project.get_or_create_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", to_project=None, merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["to_project"] == "current"

    @pytest.mark.asyncio
    async def test_2arg_mode_new_project(self):
        """Test clone_project with to_project creating new project."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})

        mock_projects = {"source": source_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        # First call fails (no current project), second call succeeds with temp session, third call fails again
        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="new-project", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["to_project"] == "new-project"
            assert result["value"]["categories_added"] == 1

    @pytest.mark.asyncio
    async def test_invalid_target_project_name(self):
        """Test clone_project with invalid target project name."""
        args = CloneProjectArgs(from_project="source", to_project="../etc")
        result_str = await clone_project(args)
        result = json.loads(result_str)

        assert result["success"] is False
        assert result["error_type"] == "invalid_name"

    @pytest.mark.asyncio
    async def test_safeguard_prevents_replace_with_existing_config(self):
        """Test safeguard prevents replace mode on non-empty target."""
        source_proj = Project(name="source", categories={}, collections={})
        target_cat = Category(name="existing", dir="src", patterns=["*.py"], description=None)
        target_proj = Project(name="target", categories={"docs": target_cat}, collections={})

        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=False, force=False)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "safeguard_prevented"
            assert "existing configuration" in result["error"]

    @pytest.mark.asyncio
    async def test_force_bypasses_safeguard(self):
        """Test force=True bypasses safeguard."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})
        target_cat = Category(name="existing", dir="src", patterns=["*.py"], description=None)
        target_proj = Project(name="target", categories={"docs": target_cat}, collections={})

        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=False, force=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["categories_added"] == 1

    @pytest.mark.asyncio
    async def test_merge_with_conflicts_shows_warnings(self):
        """Test merge mode with conflicts generates warnings."""
        source_cat = Category(dir="docs", patterns=["*.md"], description="Source docs")
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})
        target_cat = Category(name="docs", dir="documentation", patterns=["*.txt"], description="Target docs")
        target_proj = Project(name="target", categories={"docs": target_cat}, collections={})

        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert len(result["value"]["warnings"]) > 0
            assert "overwrite" in result["value"]["warnings"][0].lower()
            assert result["value"]["categories_overwritten"] == 1

    @pytest.mark.asyncio
    async def test_replace_mode_replaces_entire_config(self):
        """Test replace mode replaces entire configuration."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})
        target_proj = Project(name="target", categories={}, collections={})

        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=False, force=False)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["categories_added"] == 1
            assert result["value"]["categories_overwritten"] == 0

    @pytest.mark.asyncio
    async def test_cache_invalidated_when_current_project_modified(self):
        """Test cache is invalidated when current project is modified."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})
        current_proj = Project(name="current", categories={}, collections={})

        mock_projects = {"source": source_proj, "current": current_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.get_project = AsyncMock(return_value=current_proj)
        mock_session.save_project = AsyncMock()
        mock_session.invalidate_cache = Mock()  # Track cache invalidation

        with patch("mcp_guide.tools.tool_project.get_or_create_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", to_project="current", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            mock_session.invalidate_cache.assert_called_once()  # Cache was invalidated

    @pytest.mark.asyncio
    async def test_clone_empty_project(self):
        """Test cloning empty project."""
        source_proj = Project(name="source", categories={}, collections={})
        target_proj = Project(name="target", categories={}, collections={})

        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["categories_added"] == 0
            assert result["value"]["collections_added"] == 0

    @pytest.mark.asyncio
    async def test_clone_to_same_project(self):
        """Test cloning project to itself (idempotent)."""
        source_cat = Category(dir="docs", patterns=["*.md"], description=None)
        source_proj = Project(name="source", categories={"docs": source_cat}, collections={})

        mock_projects = {"source": source_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="source", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["categories_added"] == 0
            assert result["value"]["categories_overwritten"] == 1  # Overwrites itself

    @pytest.mark.asyncio
    async def test_clone_project_config_read_error(self):
        """clone_project returns config_read_error when get_all_projects fails."""
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(side_effect=Exception("config read failed"))

        with patch("mcp_guide.tools.tool_project.get_or_create_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", to_project="current", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "config_read_error"

    @pytest.mark.asyncio
    async def test_clone_project_config_write_error(self):
        """clone_project returns config_write_error when save_project raises OSError."""
        source_proj = Project(name="source", categories={}, collections={})
        current_proj = Project(name="current", categories={}, collections={})

        mock_projects = {"source": source_proj, "current": current_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.get_project = AsyncMock(return_value=current_proj)
        mock_session.save_project = AsyncMock(side_effect=OSError("config write failed"))

        with patch("mcp_guide.tools.tool_project.get_or_create_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", to_project="current", merge=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "config_write_error"

    @pytest.mark.asyncio
    async def test_clone_project_collection_statistics(self):
        """Exercise collection cloning/merging statistics for merge and replace modes."""
        # Source project collections: one shared with target, one source-only
        source_coll_shared = Collection(description="from source", categories=["a"])
        source_coll_only = Collection(description="source only", categories=["b"])
        source_proj = Project(
            name="source", categories={}, collections={"shared": source_coll_shared, "source_only": source_coll_only}
        )

        # Target project collections: one shared with source, one target-only
        target_coll_shared = Collection(description="from target", categories=["c"])
        target_coll_only = Collection(description="target only", categories=["d"])
        target_proj = Project(
            name="target", categories={}, collections={"shared": target_coll_shared, "target_only": target_coll_only}
        )

        # Test merge mode
        mock_projects = {"source": source_proj, "target": target_proj}
        mock_session = AsyncMock()
        mock_session.get_all_projects = AsyncMock(return_value=mock_projects)
        mock_session.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session, ValueError("No current project")],
        ):
            args = CloneProjectArgs(from_project="source", to_project="target", merge=True, force=True)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["value"]["collections_added"] == 1  # source_only
            assert result["value"]["collections_overwritten"] == 1  # shared

        # Test replace mode
        target_proj_replace = Project(
            name="target", categories={}, collections={"shared": target_coll_shared, "target_only": target_coll_only}
        )
        mock_projects_replace = {"source": source_proj, "target": target_proj_replace}
        mock_session_replace = AsyncMock()
        mock_session_replace.get_all_projects = AsyncMock(return_value=mock_projects_replace)
        mock_session_replace.save_project = AsyncMock()

        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            side_effect=[ValueError("No current project"), mock_session_replace, ValueError("No current project")],
        ):
            args_replace = CloneProjectArgs(from_project="source", to_project="target", merge=False, force=True)
            result_str_replace = await clone_project(args_replace)
            result_replace = json.loads(result_str_replace)

            assert result_replace["success"] is True
            assert result_replace["value"]["collections_added"] == 2  # Both source collections
            assert result_replace["value"]["collections_overwritten"] == 0  # Replace mode

    @pytest.mark.asyncio
    async def test_1arg_mode_no_current_project(self):
        """Test clone_project 1-arg mode when no current project is available."""
        with patch(
            "mcp_guide.tools.tool_project.get_or_create_session",
            new=AsyncMock(side_effect=ValueError("No current project")),
        ):
            args = CloneProjectArgs(from_project="source", to_project=None)
            result_str = await clone_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == "no_project"
            assert "instruction" in result
