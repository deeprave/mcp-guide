"""Unit tests for project management tools."""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.tools.base import ToolResult
from tests.helpers import create_test_session, create_unbound_test_session, request_context_for

from mcp_guide.models import Category, Collection, Project
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext, get_runtime
from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    GetCurrentProjectArgs,
    ListProjectArgs,
    ListProjectsArgs,
    SetCurrentProjectArgs,
    internal_clone_project,
    internal_get_project,
    internal_list_project,
    internal_list_projects,
    internal_set_project,
)
from mcp_guide.validation import InvalidProjectNameError


def decode_tool_result(result: object) -> dict:
    """Read the Guide payload from either the native or legacy test boundary."""
    if isinstance(result, Result):
        return result.to_json()
    if isinstance(result, ToolResult):
        assert isinstance(result.structured_content, dict)
        return result.structured_content
    assert isinstance(result, str)
    return json.JSONDecoder().decode(result)


def request_context(session, project: Project | None = None) -> RequestContext:
    """Build a RequestContext through the runtime factory for handler tests."""
    if project is not None:
        session.project = project
        session.project_is_bound = True
        session.bound_root_path = Path("/client/workspace") / project.name
        session.get_project = AsyncMock(return_value=project)
    else:
        session.project = getattr(session, "project", None)
        session.project_is_bound = False
        session.bound_root_path = None
    if not isinstance(getattr(session, "session_id", None), str):
        session.session_id = "test-session"
    return RequestContext(
        session_id=session.session_id,
        session=session,
        seq=1,
        document_path_resolver=lambda relative: Path("/docs") / relative,
    )


@pytest.fixture(autouse=True)
def explicit_runtime_session(runtime, tmp_path, monkeypatch):
    """Route public tool calls through an explicit runtime-owned test Session."""
    session = create_unbound_test_session(runtime)

    @asynccontextmanager
    async def test_request_context_scope(*_args, **_kwargs):
        yield await request_context_for(session)

    monkeypatch.setattr("mcp_guide.session.request_context_scope", test_request_context_scope)
    return session


class TestGetProject:
    """Tests for get_project tool."""

    @pytest.mark.anyio
    async def test_no_context_error(self):
        """Test get_project with no project context."""
        with patch(
            "mcp_guide.tools.tool_project.get_session_and_project",
            return_value=(MagicMock(), None),
        ):
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await internal_get_project(args, request_context(MagicMock()))
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert result["error_type"] == "no_project"

    @pytest.mark.parametrize(
        "verbose,has_data",
        [
            (False, True),  # non-verbose with data
            (True, True),  # verbose with data
            (False, False),  # empty project
        ],
    )
    @pytest.mark.anyio
    async def test_get_project_output(self, runtime, verbose: bool, has_data: bool, tmp_path: Path, monkeypatch):
        """Test get_project output format based on verbose flag and data presence."""
        project_name = "test-project" if has_data else "empty-project"
        monkeypatch.setenv("PWD", f"/fake/path/{project_name}")

        session = await create_test_session(runtime, project_name)
        context = await request_context_for(session)

        if has_data:
            # Add categories and collections
            from mcp_guide.tools.tool_category import CategoryAddArgs, internal_category_add
            from mcp_guide.tools.tool_collection import CollectionAddArgs, internal_collection_add

            await internal_category_add(
                CategoryAddArgs(name="python", dir="src/", patterns=["*.py"], description="Python source files"),
                context,
            )
            context = await request_context_for(session)
            await internal_category_add(
                CategoryAddArgs(name="typescript", dir="src/", patterns=["*.ts"], description="TypeScript files"),
                context,
            )
            context = await request_context_for(session)
            await internal_collection_add(
                CollectionAddArgs(
                    name="api-docs", description="API documentation", categories=["python", "typescript"]
                ),
                context,
            )
            context = await request_context_for(session)

        try:
            args = GetCurrentProjectArgs(verbose=verbose)
            result_str = await internal_get_project(args, context)
            result = decode_tool_result(result_str)

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
            pass

    @pytest.mark.parametrize(
        "verbose,expected_type",
        [
            (True, dict),  # verbose: flags as dict with values
            (False, list),  # non-verbose: flags as list of names
        ],
    )
    @pytest.mark.anyio
    async def test_flags_output(self, verbose: bool, expected_type: type):
        """Test get_project flag output format based on verbose flag."""
        project = Project(name="test-project", categories={}, collections={})
        session = MagicMock()

        # Mock both project and global flags
        project_flags_mock = AsyncMock()
        project_flags_mock.list = AsyncMock(return_value={"debug": True, "env": "test"})

        global_flags_mock = AsyncMock()
        global_flags_mock.list = AsyncMock(return_value={"global_flag": "value"})

        runtime = MagicMock()
        runtime.feature_flags.return_value = global_flags_mock
        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch("mcp_guide.runtime.get_runtime", return_value=runtime),
        ):
            args = GetCurrentProjectArgs(verbose=verbose)
            result_str = await internal_get_project(args, request_context(session, project))
            result = decode_tool_result(result_str)

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

    @pytest.mark.anyio
    async def test_project_flags_override_global_flags(self):
        """Test project flags take precedence over global flags."""
        project = Project(name="test-project", categories={}, collections={})
        session = MagicMock()

        # Mock both project and global flags with same name
        project_flags_mock = AsyncMock()
        project_flags_mock.list = AsyncMock(return_value={"shared_flag": "project_value"})

        global_flags_mock = AsyncMock()
        global_flags_mock.list = AsyncMock(return_value={"shared_flag": "global_value"})

        runtime = MagicMock()
        runtime.feature_flags.return_value = global_flags_mock
        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch("mcp_guide.runtime.get_runtime", return_value=runtime),
        ):
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await internal_get_project(args, request_context(session, project))
            result = decode_tool_result(result_str)

            assert result["success"] is True

            # Check project flag overrides global flag
            flags = result["value"]["flags"]
            assert flags["shared_flag"] == "project_value"


class TestSetProject:
    """Tests for set_project tool."""

    @pytest.mark.anyio
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

        with patch("mcp_guide.tools.tool_project.bind_session_project", return_value=project):
            args = SetCurrentProjectArgs(path="/client/workspace/test-project", verbose=verbose)
            result_str = await internal_set_project(args, request_context(MagicMock()))
            result = decode_tool_result(result_str)

            assert result["success"] is True
            assert result["message"] == "Bound project root for 'test-project'"

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

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "error,error_type",
        [
            (InvalidProjectNameError("must contain only alphanumeric"), "invalid_name"),
            (ValueError("must contain only alphanumeric"), "project_error"),
            (RuntimeError("Configuration file corrupted"), "project_load_error"),
        ],
    )
    async def test_set_project_errors(self, error, error_type):
        """Test error handling preserves the historical taxonomy."""
        with patch("mcp_guide.tools.tool_project.bind_session_project", side_effect=error):
            args = SetCurrentProjectArgs(path="/client/workspace/test-project", verbose=False)
            result_str = await internal_set_project(args, request_context(MagicMock()))
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert result["error_type"] == error_type
            assert str(error) in result["error"]


class TestListProjects:
    """Tests for list_projects tool."""

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
    @pytest.mark.anyio
    async def test_list_projects_success(self, verbose: bool, mock_data: dict, expected_check):
        """Test list_projects output format based on verbose flag."""
        mock_result = Result.ok(mock_data)

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=verbose)
            result_str = await internal_list_projects(args, request_context(MagicMock()))
            result = decode_tool_result(result_str)

            assert result["success"] is True
            assert expected_check(result)

    @pytest.mark.anyio
    async def test_list_projects_error(self):
        """Test list_projects propagates errors from list_all_projects."""
        mock_result = Result.failure("Failed to read configuration: Permission denied")

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=False)
            result_str = await internal_list_projects(args, request_context(MagicMock()))
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert "Failed to read configuration" in result["error"]


class TestListProject:
    """Tests for list_project tool."""

    @pytest.mark.anyio
    async def test_list_project_resolves_current_exact_key_and_unique_name(self):
        """Project lookup respects strict configuration keys and unique names."""
        current = Project(name="current", key="current-12345678", hash="1" * 64, categories={}, collections={})
        other = Project(
            name="other-project",
            key="other-project-aaaaaaaa",
            hash="a" * 64,
            categories={"docs": Category(name="docs", dir="docs", patterns=["*.md"])},
            collections={"all": Collection(name="all", categories=["docs"])},
        )
        session = AsyncMock()
        session.get_project.return_value = current
        session.project_name = "current"
        session.get_all_projects.return_value = {current.key: current, other.key: other}
        session.project_flags = MagicMock(return_value=MagicMock(list=AsyncMock(return_value={})))
        current_result = decode_tool_result(
            await internal_list_project(ListProjectArgs(), request_context(session, current))
        )
        name_result = decode_tool_result(
            await internal_list_project(
                ListProjectArgs(name="other-project", verbose=True), request_context(session, current)
            )
        )
        key_result = decode_tool_result(
            await internal_list_project(ListProjectArgs(name=other.key), request_context(session, current))
        )

        assert current_result["success"] is True
        assert name_result["value"]["project"] == "other-project"
        assert isinstance(name_result["value"]["categories"], dict)
        assert key_result["value"]["project"] == "other-project"

    @pytest.mark.anyio
    async def test_list_project_project_not_found(self):
        """Test list_project error propagation."""

        session = AsyncMock()
        session.get_all_projects.return_value = {}
        args = ListProjectArgs(name="nonexistent", verbose=False)
        result = decode_tool_result(await internal_list_project(args, request_context(session)))

        assert result["success"] is False
        assert "not found" in result["error"]


class TestCloneProjectArgs:
    """Tests for CloneProjectArgs schema."""

    def test_clone_target_is_not_a_public_argument(self):
        """Cloning always targets the root-bound current project."""
        args = CloneProjectArgs(from_project="source", to_project="target")
        assert "to_project" not in CloneProjectArgs.model_fields
        assert "to_project" not in args.model_dump()


class TestCloneProject:
    """Tests for clone_project tool."""

    @pytest.mark.anyio
    async def test_clone_project_source_resolution_errors(self):
        """Invalid, missing, and ambiguous sources are rejected before mutation."""
        current = Project(name="current", key="current-12345678", hash="12345678", categories={}, collections={})
        session = AsyncMock()
        session.get_project.return_value = current

        async def resolve_source(name: str):
            if name == "source":
                return None, ["source-aaaaaaaa", "source-bbbbbbbb"]
            return None, []

        session.resolve_clone_source.side_effect = resolve_source
        session.get_all_projects.return_value = {
            "current-12345678": current,
            "source-aaaaaaaa": Project(name="source", key="source-aaaaaaaa", hash="a" * 64),
            "source-bbbbbbbb": Project(name="source", key="source-bbbbbbbb", hash="b" * 64),
        }
        context = request_context(session, current)
        invalid = decode_tool_result(await internal_clone_project(CloneProjectArgs(from_project="../etc"), context))
        missing = decode_tool_result(await internal_clone_project(CloneProjectArgs(from_project="missing"), context))
        ambiguous = decode_tool_result(await internal_clone_project(CloneProjectArgs(from_project="source"), context))

        assert invalid["error_type"] == "invalid_name"
        assert missing["error_type"] == "not_found"
        assert ambiguous["error_type"] == "not_found"
        assert "source-aaaaaaaa" in ambiguous["error"]
        assert "source-bbbbbbbb" in ambiguous["error"]

    @pytest.mark.anyio
    async def test_clone_project_uses_exact_source_key_before_name_resolution(self):
        """A generated source key remains unambiguous even when names repeat."""
        source = Project(name="source", key="source-aaaaaaaa", hash="a" * 64, categories={}, collections={})
        current = Project(name="current", key="current-12345678", hash="1" * 64, categories={}, collections={})
        session = AsyncMock()
        session.get_project.return_value = current
        session.resolve_clone_source.return_value = (source, [])
        session.get_all_projects.return_value = {
            source.key: source,
            "source-bbbbbbbb": Project(name="source", key="source-bbbbbbbb", hash="b" * 64),
            current.key: current,
        }
        result = decode_tool_result(
            await internal_clone_project(CloneProjectArgs(from_project=source.key), request_context(session, current))
        )

        assert result["success"] is True
        assert result["value"]["to_project"] == "current"
        session.save_project.assert_awaited_once()

    @pytest.mark.anyio
    async def test_config_write_error(self):
        """clone_project returns config_write_error when save_project raises OSError."""
        source_proj = Project(name="source", categories={}, collections={})
        current_proj = Project(name="current", categories={}, collections={})

        mock_projects = {"source": source_proj, "current": current_proj}
        mock_session = AsyncMock()
        mock_session.resolve_clone_source = AsyncMock(return_value=(source_proj, []))
        mock_session.get_project = AsyncMock(return_value=current_proj)
        mock_session.save_project = AsyncMock(side_effect=OSError("config write failed"))

        args = CloneProjectArgs(from_project="source", merge=True)
        result = decode_tool_result(await internal_clone_project(args, request_context(mock_session, current_proj)))

        assert result["success"] is False
        assert result["error_type"] == "config_write_error"

    @pytest.mark.anyio
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
        mock_session.resolve_clone_source = AsyncMock(return_value=(source_proj, []))
        mock_session.save_project = AsyncMock()

        mock_session.get_project = AsyncMock(return_value=target_proj)
        args = CloneProjectArgs(from_project="source", merge=True, force=True)
        result = decode_tool_result(await internal_clone_project(args, request_context(mock_session, target_proj)))

        assert result["success"] is True
        assert result["value"]["collections_added"] == 1  # source_only
        assert result["value"]["collections_overwritten"] == 1  # shared

        # Test replace mode
        target_proj_replace = Project(
            name="target", categories={}, collections={"shared": target_coll_shared, "target_only": target_coll_only}
        )
        mock_projects_replace = {"source": source_proj, "target": target_proj_replace}
        mock_session_replace = AsyncMock()
        mock_session_replace.resolve_clone_source = AsyncMock(return_value=(source_proj, []))
        mock_session_replace.save_project = AsyncMock()

        mock_session_replace.get_project = AsyncMock(return_value=target_proj_replace)
        args_replace = CloneProjectArgs(from_project="source", merge=False, force=True)
        result_replace = decode_tool_result(
            await internal_clone_project(args_replace, request_context(mock_session_replace, target_proj_replace))
        )

        assert result_replace["success"] is True
        assert result_replace["value"]["collections_added"] == 2  # Both source collections
        assert result_replace["value"]["collections_overwritten"] == 0  # Replace mode

    @pytest.mark.anyio
    async def test_1arg_mode_no_current_project(self):
        """clone_project requires a bound current project."""
        args = CloneProjectArgs(from_project="source")
        result = decode_tool_result(await internal_clone_project(args, request_context(MagicMock())))

        assert result["success"] is False
        assert result["error_type"] == "no_project"
        assert "instruction" in result

    @pytest.mark.anyio
    async def test_clone_safeguard_uses_reloaded_dirty_project(self, runtime, tmp_path: Path):
        """Replace-mode clone consults the reloaded Project, not a stale empty snapshot."""
        from mcp_guide.runtime import OwnerKey
        from mcp_guide.session import bind_session_project

        session = await create_test_session(runtime, "target")
        await session.update_config(
            lambda project: project.with_category("docs", Category(dir="docs", patterns=["*.md"]))
        )
        source_session = get_runtime().resolve_session(OwnerKey("source-owner"))
        await bind_session_project(source_session, "/client/workspace/source")

        current = session.project
        assert current is not None
        stale = Project(
            name=current.name,
            key=current.key,
            hash=current.hash,
            categories={},
            collections={},
        )
        session._Session__delegate.bind(stale)  # ty: ignore[attr-defined]
        session._project_dirty = True

        result = decode_tool_result(
            await internal_clone_project(
                CloneProjectArgs(from_project="source", merge=False, force=False),
                await request_context_for(session),
            )
        )

        assert result["success"] is False
        assert result["error_type"] == "safeguard_prevented"
