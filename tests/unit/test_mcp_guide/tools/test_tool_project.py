"""Unit tests for project management tools."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.tools.base import ToolResult
from tests.helpers import create_test_runtime, create_test_session, create_unbound_test_session

from mcp_guide.models import Category, Collection, Project
from mcp_guide.result import Result
from mcp_guide.runtime import OwnerKey
from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    GetCurrentProjectArgs,
    ListProjectArgs,
    ListProjectsArgs,
    SetCurrentProjectArgs,
    clone_project,
    get_project,
    internal_set_project,
    list_project,
    list_projects,
    set_project,
)


def decode_tool_result(result: object) -> dict:
    """Read the Guide payload from either the native or legacy test boundary."""
    if isinstance(result, ToolResult):
        assert isinstance(result.structured_content, dict)
        return result.structured_content
    assert isinstance(result, str)
    return json.JSONDecoder().decode(result)


@pytest.fixture(autouse=True)
def explicit_runtime_session(tmp_path, monkeypatch):
    """Route direct decorated-tool calls through a runtime-owned test Session."""
    session = create_unbound_test_session(str(tmp_path))

    async def get_test_session(*_args, **_kwargs):
        return session

    monkeypatch.setattr("mcp_guide.core.tool_decorator.get_session", get_test_session)
    monkeypatch.setattr("mcp_guide.tools.tool_project.get_session", get_test_session)
    return session


@pytest.mark.anyio
async def test_failed_modern_binding_retires_its_minted_fastmcp_session(monkeypatch) -> None:
    """A session minted for a failed bind must not remain in FastMCP's store."""
    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.tools.tool_project as tool_project_module

    class FakeContext:
        def __init__(self) -> None:
            self.request_context = MagicMock(protocol_version="2026-07-28")

    create_session = AsyncMock(return_value="minted-session")
    end_session = AsyncMock()
    runtime = MagicMock()
    runtime.discard_session = AsyncMock()
    monkeypatch.setattr(tool_project_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)
    monkeypatch.setattr(fastmcp_sessions, "end_session", end_session)
    monkeypatch.setattr("mcp_guide.mcp_context.runtime_from_fastmcp", lambda _ctx: runtime)
    monkeypatch.setattr(
        tool_project_module,
        "session_set_project",
        AsyncMock(return_value=Result.failure("invalid project root", error_type="invalid_project")),
    )

    result = await internal_set_project(SetCurrentProjectArgs(path="/invalid/project"), FakeContext())

    assert not result.is_ok()
    end_session.assert_awaited_once_with("minted-session")
    runtime.discard_session.assert_awaited_once()
    assert runtime.discard_session.await_args.args[0] == OwnerKey("minted-session")


@pytest.mark.anyio
async def test_modern_binding_records_its_minted_session_id_on_the_arguments(monkeypatch) -> None:
    """The outer result adapter must resolve the Session that was just bound."""
    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.tools.tool_project as tool_project_module

    class FakeContext:
        def __init__(self) -> None:
            self.request_context = MagicMock(protocol_version="2026-07-28")

    project = Project(name="project", categories={}, collections={})
    session = MagicMock()
    monkeypatch.setattr(tool_project_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", AsyncMock(return_value="minted-session"))
    monkeypatch.setattr(tool_project_module, "session_set_project", AsyncMock(return_value=Result.ok(project)))
    monkeypatch.setattr(tool_project_module, "get_session", AsyncMock(return_value=session))

    args = SetCurrentProjectArgs(path="/client/project")
    result = await internal_set_project(args, FakeContext())

    assert result.is_ok()
    assert args.session_id == "minted-session"


class TestGetProject:
    """Tests for get_project tool."""

    @pytest.mark.anyio
    async def test_stdio_pwd_bootstrap_mints_and_returns_a_modern_session_id(self, tmp_path, monkeypatch) -> None:
        """The first stdio tool response resumes the Session created from PWD."""
        import fastmcp.server.sessions as fastmcp_sessions

        import mcp_guide.core.tool_decorator as tool_decorator_module
        import mcp_guide.session as session_module
        import mcp_guide.tools.tool_helpers as tool_helpers_module
        import mcp_guide.tools.tool_project as tool_project_module
        from mcp_guide.runtime import OwnerKey

        class FakeContext:
            def __init__(self, runtime) -> None:
                self.request_context = SimpleNamespace(
                    protocol_version="2026-07-28",
                    request_id="stdio-bootstrap",
                    meta=None,
                    lifespan_context=runtime,
                )
                self.session = SimpleNamespace(client_params=None)
                self.transport = "stdio"

        project_root = tmp_path / "stdio-project"
        project_root.mkdir()
        runtime = create_test_runtime(str(tmp_path / "config"))
        context = FakeContext(runtime)
        create_session = AsyncMock(return_value="minted-stdio-session")
        get_fastmcp_session = AsyncMock(return_value=object())
        monkeypatch.setenv("PWD", str(project_root))
        monkeypatch.setattr(session_module, "Context", FakeContext)
        monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)
        monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)
        monkeypatch.setattr(tool_decorator_module, "get_session", session_module.get_session)
        monkeypatch.setattr(tool_helpers_module, "get_session", session_module.get_session)
        monkeypatch.setattr(tool_project_module, "get_session", session_module.get_session)

        result = await get_project(GetCurrentProjectArgs(), context)
        payload = decode_tool_result(result)
        session = runtime.resolve_session(OwnerKey("minted-stdio-session"))

        assert payload["session_id"] == "minted-stdio-session"
        assert session.bound_root_path == project_root
        assert session.session_id == "minted-stdio-session"
        create_session.assert_awaited_once()
        get_fastmcp_session.assert_awaited()
        await session.cleanup()

    @pytest.mark.anyio
    async def test_no_context_error(self):
        """Test get_project with no project context."""
        with patch(
            "mcp_guide.tools.tool_project.get_session_and_project",
            return_value=(MagicMock(), None),
        ):
            args = GetCurrentProjectArgs(verbose=False)
            result_str = await get_project(args)
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
    async def test_get_project_output(self, verbose: bool, has_data: bool, tmp_path: Path, monkeypatch):
        """Test get_project output format based on verbose flag and data presence."""
        project_name = "test-project" if has_data else "empty-project"
        monkeypatch.setenv("PWD", f"/fake/path/{project_name}")

        session = await create_test_session(project_name, _config_dir_for_tests=str(tmp_path))
        await session.get_project()

        async def get_bound_session_and_project(_ctx=None, *, session_id=None):
            return session, await session.get_project()

        monkeypatch.setattr(
            "mcp_guide.tools.tool_project.get_session_and_project",
            get_bound_session_and_project,
        )
        monkeypatch.setattr(
            "mcp_guide.tools.tool_category.get_session_and_project",
            get_bound_session_and_project,
        )
        monkeypatch.setattr(
            "mcp_guide.tools.tool_collection.get_session_and_project",
            get_bound_session_and_project,
        )

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

        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch.object(session.runtime, "feature_flags", return_value=global_flags_mock),
            patch("mcp_guide.tools.tool_project.get_session_and_project", return_value=(session, project)),
        ):
            args = GetCurrentProjectArgs(verbose=verbose)
            result_str = await get_project(args)
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

        with (
            patch.object(session, "project_flags", return_value=project_flags_mock),
            patch.object(session.runtime, "feature_flags", return_value=global_flags_mock),
            patch("mcp_guide.tools.tool_project.get_session_and_project", return_value=(session, project)),
        ):
            args = GetCurrentProjectArgs(verbose=True)
            result_str = await get_project(args)
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

        with patch("mcp_guide.tools.tool_project.session_set_project", return_value=mock_result):
            args = SetCurrentProjectArgs(path="/client/workspace/test-project", verbose=verbose)
            result_str = await set_project(args)
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
            args = SetCurrentProjectArgs(path="/client/workspace/test-project", verbose=False)
            result_str = await set_project(args)
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert result["error_type"] == error_type
            assert error_msg in result["error"]


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
            result_str = await list_projects(args)
            result = decode_tool_result(result_str)

            assert result["success"] is True
            assert expected_check(result)

    @pytest.mark.anyio
    async def test_list_projects_error(self):
        """Test list_projects propagates errors from list_all_projects."""
        mock_result = Result.failure("Failed to read configuration: Permission denied")

        with patch("mcp_guide.tools.tool_project.list_all_projects", return_value=mock_result):
            args = ListProjectsArgs(verbose=False)
            result_str = await list_projects(args)
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
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=session)):
            current_result = decode_tool_result(await list_project(ListProjectArgs()))
            name_result = decode_tool_result(await list_project(ListProjectArgs(name="other-project", verbose=True)))
            key_result = decode_tool_result(await list_project(ListProjectArgs(name=other.key)))

        assert current_result["success"] is True
        assert name_result["value"]["project"] == "other-project"
        assert isinstance(name_result["value"]["categories"], dict)
        assert key_result["value"]["project"] == "other-project"

    @pytest.mark.anyio
    async def test_list_project_project_not_found(self):
        """Test list_project error propagation."""

        session = AsyncMock()
        session.get_all_projects.return_value = {}
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=session)):
            args = ListProjectArgs(name="nonexistent", verbose=False)
            result_str = await list_project(args)
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert "not found" in result["error"]


class TestCloneProjectArgs:
    """Tests for CloneProjectArgs schema."""

    def test_clone_target_is_not_a_public_argument(self):
        """Cloning always targets the root-bound current project."""
        with pytest.raises(ValueError, match="to_project"):
            CloneProjectArgs(from_project="source", to_project="target")


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
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=session)):
            invalid = decode_tool_result(await clone_project(CloneProjectArgs(from_project="../etc")))
            missing = decode_tool_result(await clone_project(CloneProjectArgs(from_project="missing")))
            ambiguous = decode_tool_result(await clone_project(CloneProjectArgs(from_project="source")))

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
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=session)):
            result = decode_tool_result(await clone_project(CloneProjectArgs(from_project=source.key)))

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

        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", merge=True)
            result_str = await clone_project(args)
            result = decode_tool_result(result_str)

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
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=mock_session)):
            args = CloneProjectArgs(from_project="source", merge=True, force=True)
            result_str = await clone_project(args)
            result = decode_tool_result(result_str)

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
        with patch("mcp_guide.tools.tool_project.get_session", new=AsyncMock(return_value=mock_session_replace)):
            args_replace = CloneProjectArgs(from_project="source", merge=False, force=True)
            result_str_replace = await clone_project(args_replace)
            result_replace = decode_tool_result(result_str_replace)

            assert result_replace["success"] is True
            assert result_replace["value"]["collections_added"] == 2  # Both source collections
            assert result_replace["value"]["collections_overwritten"] == 0  # Replace mode

    @pytest.mark.anyio
    async def test_1arg_mode_no_current_project(self):
        """clone_project requires a bound current project."""
        with patch(
            "mcp_guide.tools.tool_project.get_session",
            new=AsyncMock(side_effect=ValueError("No current project")),
        ):
            args = CloneProjectArgs(from_project="source")
            result_str = await clone_project(args)
            result = decode_tool_result(result_str)

            assert result["success"] is False
            assert result["error_type"] == "no_project"
            assert "instruction" in result
