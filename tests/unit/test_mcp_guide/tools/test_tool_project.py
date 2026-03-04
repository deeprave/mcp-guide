"""Unit tests for project management tools."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.models import Category, Collection, Project
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_SAFEGUARD
from mcp_guide.session import Session, remove_current_session, set_current_session
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

    @pytest.mark.parametrize(
        "verbose,has_data",
        [
            (False, True),  # non-verbose with data
            (True, True),  # verbose with data
            (False, False),  # empty project
        ],
    )
    @pytest.mark.asyncio
    async def test_get_project_output(self, verbose: bool, has_data: bool, tmp_path: Path, monkeypatch):
        """Test get_project output format based on verbose flag and data presence."""
        project_name = "test-project" if has_data else "empty-project"
        monkeypatch.setenv("PWD", f"/fake/path/{project_name}")

        session = Session(project_name, _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        set_current_session(session)

        if has_data:
            # Add categories and collections
            from mcp_guide.tools.tool_category import CategoryAddArgs, internal_category_add
            from mcp_guide.tools.tool_collection import CollectionAddArgs, internal_collection_add

            await internal_category_add(
                CategoryAddArgs(name="python", dir="src/", patterns=["*.py"], description="Python source files")
            )
            await internal_category_add(
                CategoryAddArgs(name="typescript", dir="src/", patterns=["*.ts"], description="TypeScript files")
            )
            await internal_collection_add(
                CollectionAddArgs(name="api-docs", description="API documentation", categories=["python", "typescript"])
            )

        try:
            args = GetCurrentProjectArgs(verbose=verbose)
            result_str = await get_project(args)
            result = json.loads(result_str)

            assert result["success"] is True

            if has_data:
                if verbose:
                    # Verbose mode: full details as dicts
                    assert len(result["value"]["collections"]) == 1
                    collection = result["value"]["collections"][0]
                    assert collection["name"] == "api-docs"
                    assert collection["description"] == "API documentation"
                    assert set(collection["categories"]) == {"python", "typescript"}

                    assert len(result["value"]["categories"]) == 2
                    category_names = {c["name"] for c in result["value"]["categories"]}
                    assert category_names == {"python", "typescript"}
                    for category in result["value"]["categories"]:
                        assert all(k in category for k in ["name", "dir", "patterns", "description"])
                else:
                    # Non-verbose mode: names only as strings
                    assert result["value"]["collections"] == ["api-docs"]
                    assert set(result["value"]["categories"]) == {"python", "typescript"}
                    assert all(isinstance(c, str) for c in result["value"]["collections"])
                    assert all(isinstance(c, str) for c in result["value"]["categories"])
            else:
                # Empty project
                assert result["value"]["collections"] == []
                assert result["value"]["categories"] == []
        finally:
            await remove_current_session(project_name)

    @pytest.mark.parametrize(
        "verbose,expected_type",
        [
            (True, dict),  # verbose: flags as dict with values
            (False, list),  # non-verbose: flags as list of names
        ],
    )
    @pytest.mark.asyncio
    async def test_flags_output(self, verbose: bool, expected_type: type, tmp_path: Path, monkeypatch):
        """Test get_project flag output format based on verbose flag."""
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        set_current_session(session)

        # Mock both project and global flags
        project_flags_mock = AsyncMock()
        project_flags_mock.list = AsyncMock(return_value={"debug": True, "env": "test"})

        global_flags_mock = AsyncMock()
        global_flags_mock.list = AsyncMock(return_value={"global_flag": "value"})

        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch.object(session, "feature_flags", return_value=global_flags_mock),
        ):
            try:
                args = GetCurrentProjectArgs(verbose=verbose)
                result_str = await get_project(args)
                result = json.loads(result_str)

                assert result["success"] is True
                flags = result["value"]["flags"]
                assert isinstance(flags, expected_type)

                if verbose:
                    # Verbose: dict with values
                    assert flags["debug"] is True
                    assert flags["env"] == "test"
                    assert flags["global_flag"] == "value"
                else:
                    # Non-verbose: list of names
                    assert set(flags) == {"debug", "env", "global_flag"}
            finally:
                await remove_current_session("test-project")

    @pytest.mark.asyncio
    async def test_project_flags_override_global_flags(self, tmp_path: Path, monkeypatch):
        """Test project flags take precedence over global flags."""
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        set_current_session(session)

        # Mock both project and global flags with same name
        project_flags_mock = AsyncMock()
        project_flags_mock.list = AsyncMock(return_value={"shared_flag": "project_value"})

        global_flags_mock = AsyncMock()
        global_flags_mock.list = AsyncMock(return_value={"shared_flag": "global_value"})

        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch.object(session, "feature_flags", return_value=global_flags_mock),
        ):
            try:
                args = GetCurrentProjectArgs(verbose=True)
                result_str = await get_project(args)
                result = json.loads(result_str)

                assert result["success"] is True

                # Check project flag overrides global flag
                flags = result["value"]["flags"]
                assert flags["shared_flag"] == "project_value"
            finally:
                await remove_current_session("test-project")


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
    @pytest.mark.parametrize(
        "scenario,verbose,has_data",
        [
            ("existing_non_verbose", False, True),
            ("existing_verbose", True, True),
            ("create_new", False, False),
        ],
    )
    async def test_set_project_success(self, scenario: str, verbose: bool, has_data: bool):
        """Test successful project switching."""
        # Create mock project
        if has_data:
            project = Project(
                name="test-project",
                categories={
                    "python": Category(dir="src/", patterns=["*.py"], description="Python files"),
                    "docs": Category(dir="docs/", patterns=["*.md"], description="Documentation"),
                },
                collections={"backend": Collection(categories=["python"], description="Backend code")},
            )
        else:
            project = Project(name="test-project", categories={}, collections={})

        mock_result = Result.ok(project)

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="test-project", verbose=verbose)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert result["message"] == "Switched to project 'test-project'"

            if verbose and has_data:
                assert len(result["value"]["collections"]) == 1
                assert result["value"]["collections"][0]["name"] == "backend"
                assert len(result["value"]["categories"]) == 2
            elif has_data:
                assert result["value"]["collections"] == ["backend"]
                assert result["value"]["categories"] == ["python", "docs"]
            else:
                assert result["value"]["collections"] == []
                assert result["value"]["categories"] == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error_type,error_msg",
        [
            ("invalid_name", "must contain only alphanumeric"),
            ("project_load_error", "Configuration file corrupted"),
        ],
    )
    async def test_set_project_errors(self, error_type: str, error_msg: str):
        """Test error handling."""
        mock_result = Result.failure(error_msg, error_type=error_type)

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(name="test-project", verbose=False)
            result_str = await set_project(args)
            result = json.loads(result_str)

            assert result["success"] is False
            assert result["error_type"] == error_type
            assert error_msg in result["error"]


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

    @pytest.mark.parametrize(
        "verbose,mock_data,expected_check",
        [
            (
                False,
                {"projects": ["alpha", "beta", "gamma"]},
                lambda r: r["value"]["projects"] == ["alpha", "beta", "gamma"],
            ),
            (
                True,
                {
                    "projects": {
                        "project1": {"categories": [], "collections": []},
                        "project2": {"categories": [], "collections": []},
                    }
                },
                lambda r: "project1" in r["value"]["projects"] and "project2" in r["value"]["projects"],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_list_projects_success(self, verbose: bool, mock_data: dict, expected_check):
        """Test list_projects output format based on verbose flag."""
        mock_result = Result.ok(mock_data)

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=verbose)
            result_str = await list_projects(args)
            result = json.loads(result_str)

            assert result["success"] is True
            assert expected_check(result)

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

    @pytest.mark.parametrize(
        "name,verbose,mock_setup",
        [
            (None, False, lambda: patch("mcp_guide.tools.tool_project.get_or_create_session")),  # current project
            (
                "other-project",
                False,
                lambda: patch(
                    "mcp_guide.session.Session.get_project_config",
                    new=AsyncMock(return_value=Project(name="other-project", categories={}, collections={})),
                ),
            ),  # specific project
            (
                "test-project",
                True,
                lambda: patch(
                    "mcp_guide.session.Session.get_project_config",
                    new=AsyncMock(
                        return_value=Project(
                            name="test-project",
                            categories={"docs": Category(name="docs", dir="docs", patterns=["*.md"])},
                            collections={"all": Collection(name="all", categories=["docs"])},
                        )
                    ),
                ),
            ),  # verbose mode
        ],
    )
    @pytest.mark.asyncio
    async def test_list_project_success(self, name, verbose, mock_setup):
        """Test list_project with different name and verbose combinations."""
        from mcp_guide.models import Project

        with mock_setup() as mock:
            if name is None:
                # Current project case
                mock.return_value.get_project.return_value = Project(name="test", categories={}, collections={})
                mock.return_value.project_name = "test"

            args = ListProjectArgs(name=name, verbose=verbose)
            result_str = await list_project(args)
            result = json.loads(result_str)

            assert result["success"] is True
            if verbose:
                assert isinstance(result["value"]["categories"], dict)

    @pytest.mark.asyncio
    async def test_list_project_project_not_found(self):
        """Test list_project error propagation."""

        with patch(
            "mcp_guide.session.Session.get_project_config",
            new=AsyncMock(side_effect=ValueError("Project 'nonexistent' not found")),
        ):
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
    @pytest.mark.parametrize(
        "error_type,from_project,to_project,mock_setup,expected_error_type,expected_msg",
        [
            (
                "source_not_found",
                "nonexistent",
                None,
                lambda: patch(
                    "mcp_guide.tools.tool_project.get_or_create_session",
                    new=AsyncMock(
                        return_value=AsyncMock(
                            get_all_projects=AsyncMock(
                                return_value={"existing": Project(name="existing", categories={}, collections={})}
                            )
                        )
                    ),
                ),
                "not_found",
                "not found",
            ),
            ("invalid_source_name", "../etc", None, None, "invalid_name", None),
            ("invalid_target_name", "source", "../etc", None, "invalid_name", None),
            (
                "config_read_error",
                "source",
                "current",
                lambda: patch(
                    "mcp_guide.tools.tool_project.get_or_create_session",
                    new=AsyncMock(
                        return_value=AsyncMock(get_all_projects=AsyncMock(side_effect=Exception("config read failed")))
                    ),
                ),
                "config_read_error",
                None,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_clone_project_errors(
        self, error_type, from_project, to_project, mock_setup, expected_error_type, expected_msg
    ):
        """Test clone_project error scenarios."""
        if mock_setup:
            with mock_setup():
                args = CloneProjectArgs(from_project=from_project, to_project=to_project)
                result_str = await clone_project(args)
                result = json.loads(result_str)
        else:
            args = CloneProjectArgs(from_project=from_project, to_project=to_project)
            result_str = await clone_project(args)
            result = json.loads(result_str)

        assert result["success"] is False
        assert result["error_type"] == expected_error_type
        if expected_msg:
            assert expected_msg in result["error"].lower()

    @pytest.mark.asyncio
    async def test_config_write_error(self):
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
