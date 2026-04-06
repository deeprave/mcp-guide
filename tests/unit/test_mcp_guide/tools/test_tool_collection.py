"""Tests for collection management tools."""

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from tests.helpers import create_bound_test_session

from mcp_guide.models import Category, Collection
from mcp_guide.session import (
    Session,
    get_session,
    remove_current_session,
    set_current_session,
)
from mcp_guide.tools.tool_collection import (
    CollectionAddArgs,
    CollectionListArgs,
    internal_collection_add,
    internal_collection_list,
)


@pytest.fixture(scope="module")
async def test_session_with_data(tmp_path_factory):
    """Module-level fixture providing a session with sample data."""
    tmp_path = tmp_path_factory.mktemp("collection_tests")
    session = await create_bound_test_session("test", _config_dir_for_tests=str(tmp_path))
    set_current_session(session)

    # Seed the bound project directly. These tests need stable in-memory data
    # for list/change behavior; persistence is covered elsewhere.
    project = session._Session__delegate.project  # ty: ignore[attr-defined]
    session._Session__delegate.bind(  # ty: ignore[attr-defined]
        project.with_category("docs", Category(dir="documentation", patterns=["*.md"]))
        .with_category("api", Category(dir="api", patterns=["*.json"]))
        .with_category("tests", Category(dir="tests", patterns=["*.py"]))
        .with_collection("backend", Collection(categories=["api", "tests"], description="Backend code"))
        .with_collection("documentation", Collection(categories=["docs"], description="All docs"))
        .with_collection("empty", Collection(categories=[], description="Empty collection"))
    )

    yield session
    await remove_current_session()


@pytest.fixture(autouse=True)
async def setup_session(test_session_with_data, monkeypatch):
    """Auto-use fixture to ensure session is set for each test."""
    set_current_session(test_session_with_data)
    monkeypatch.setenv("PWD", "/fake/path/test")
    yield


class TestCollectionList:
    """Tests for collection_list tool."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("verbose", "expected"),
        [
            (
                True,
                [
                    {
                        "name": "backend",
                        "categories": ["api", "tests"],
                        "description": "Backend code",
                    },
                    {
                        "name": "documentation",
                        "categories": ["docs"],
                        "description": "All docs",
                    },
                    {
                        "name": "empty",
                        "categories": [],
                        "description": "Empty collection",
                    },
                ],
            ),
            (False, ["backend", "documentation", "empty"]),
        ],
        ids=["verbose", "names_only"],
    )
    async def test_collection_list_respects_verbose_flag(self, verbose: bool, expected: list[object]) -> None:
        """collection_list should switch between detail and name-only output."""
        args = CollectionListArgs(verbose=verbose)
        result = await internal_collection_list(args)

        assert result.success is True
        assert result.value == expected

    @pytest.mark.anyio
    async def test_empty_collections_returns_empty_list(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Empty collections list should return empty list."""
        # Clear collections for this test
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionListArgs()
        result = await internal_collection_list(args)

        assert result.success is True
        assert result.value == []

    @pytest.mark.anyio
    async def test_collection_with_empty_categories(self, test_session_with_data: Session) -> None:
        """Collection with empty categories list should return empty list in categories field."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        project.collections["empty"] = Collection(categories=[], description="No categories")
        await session.save_project(project)

        args = CollectionListArgs(verbose=True)
        result = await internal_collection_list(args)

        assert result.success is True
        assert len(result.value) == 1
        assert result.value[0]["categories"] == []

    @pytest.mark.anyio
    async def test_no_active_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        # Clear current session and unset PWD/CWD so get_session fails
        await remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionListArgs()
        result = await internal_collection_list(args)

        assert result.success is False
        assert result.error_type == "no_project"


class TestCollectionAdd:
    """Tests for collection_add tool."""

    @pytest.mark.anyio
    async def test_add_collection_name_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with just name."""
        # Clear existing collections for this test
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionAddArgs(name="backend")
        result = await internal_collection_add(args)

        assert result.success is True
        assert "backend" in result.value
        assert "added successfully" in result.value

        # Verify collection exists in project
        project = await session.get_project()
        assert len(project.collections) == 1
        assert "backend" in project.collections
        assert project.collections["backend"].categories == []
        assert project.collections["backend"].description is None

    @pytest.mark.anyio
    async def test_add_collection_with_description(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with name and description."""
        # Clear existing collections for this test
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionAddArgs(name="docs", description="Documentation files")
        result = await internal_collection_add(args)

        assert result.success is True

        # Verify description is set
        project = await session.get_project()
        assert len(project.collections) == 1
        assert "docs" in project.collections
        assert project.collections["docs"].description == "Documentation files"

    @pytest.mark.anyio
    async def test_add_collection_with_categories(self, test_session_with_data: Session) -> None:
        """Create collection with valid categories."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        args = CollectionAddArgs(name="backend", categories=["api", "tests"])
        result = await internal_collection_add(args)

        assert result.success is True

        # Verify categories are set
        project = await session.get_project()
        assert len(project.collections) == 1
        assert "backend" in project.collections
        assert project.collections["backend"].categories == ["api", "tests"]

    @pytest.mark.anyio
    async def test_add_collection_deduplicates_categories(self, test_session_with_data: Session) -> None:
        """Duplicate categories should be deduplicated while preserving order."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        # Pass duplicates: api, tests, api, docs, tests
        args = CollectionAddArgs(name="backend", categories=["api", "tests", "api", "docs", "tests"])
        result = await internal_collection_add(args)

        assert result.success is True

        # Verify only unique categories stored, order preserved
        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests", "docs"]

    @pytest.mark.anyio
    async def test_add_collection_duplicate_name_error(self, test_session_with_data: Session) -> None:
        """Duplicate collection name should return validation error."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        # Add existing collection via proper API
        await session.update_config(lambda p: p.with_collection("backend", Collection(categories=[], description="")))

        # Capture original project state
        original_project = await session.get_project()
        original_collections = original_project.collections

        args = CollectionAddArgs(name="backend")
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "already exists" in result.error

        # Project state should be unchanged after failed validation
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)
        assert project.collections == original_collections

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "description,error_contains",
        [
            ("x" * 501, "exceeds"),
            ('Has "quotes" in it', "quote"),
        ],
        ids=["too_long", "quotes"],
    )
    async def test_add_collection_invalid_description(
        self, test_session_with_data: Session, description: str, error_contains: str
    ) -> None:
        """Description validation should reject invalid values."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        original_project = await session.get_project()
        original_collections = original_project.collections

        args = CollectionAddArgs(name="backend", description=description)
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert error_contains in result.error

        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.anyio
    async def test_add_collection_nonexistent_categories(self, test_session_with_data: Session) -> None:
        """Non-existent categories should return validation error."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)
        # Add one category via proper API
        await session.update_config(lambda p: p.with_category("api", Category(dir="api", patterns=["*.py"])))

        # Capture original project state
        original_project = await session.get_project()
        original_collections = original_project.collections

        args = CollectionAddArgs(name="backend", categories=["api", "nonexistent"])
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "does not exist" in result.error

        # Project state should be unchanged
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.anyio
    async def test_add_collection_no_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session should return error."""
        await remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionAddArgs(name="backend")
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "no_project"

    @pytest.mark.anyio
    async def test_add_collection_invalid_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Invalid collection name should return validation error."""
        from mcp_guide.session import get_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        # Capture original project state
        original_project = await session.get_project()
        original_collections = original_project.collections

        # Test name too long
        args = CollectionAddArgs(name="x" * 31)
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"

        # Project state should be unchanged
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.anyio
    async def test_add_collection_underscore_prefix_rejected(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Collection names starting with underscore should be rejected."""
        from mcp_guide.session import get_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        args = CollectionAddArgs(name="_system")
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "underscore" in result.error.lower()

    @pytest.mark.anyio
    async def test_add_collection_save_error(self, test_session_with_data: Session, monkeypatch: MonkeyPatch) -> None:
        """Configuration save failure should return ERROR_SAVE."""
        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        # Mock update_config to raise an exception
        async def mock_update_config(*args, **kwargs):  # type: ignore
            raise RuntimeError("Simulated save failure")

        monkeypatch.setattr(session, "update_config", mock_update_config)

        args = CollectionAddArgs(name="backend")
        result = await internal_collection_add(args)

        assert result.success is False
        assert result.error_type == "save_error"
        assert "Failed to save" in result.error


class TestCollectionRemove:
    """Tests for collection_remove tool."""

    @pytest.mark.anyio
    async def test_collection_remove_existing(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Remove existing collection."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = {"name": "backend", "categories": ["api"], "description": "Backend"}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionRemoveArgs(name="backend")
        result = await internal_collection_remove(args)

        assert result.success is True
        assert "removed successfully" in result.value

        project = await session.get_project()
        assert len(project.collections) == 0

    @pytest.mark.anyio
    async def test_collection_remove_nonexistent(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject removing non-existent collection."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionRemoveArgs(name="nonexistent")
        result = await internal_collection_remove(args)

        assert result.success is False
        assert result.error_type == "not_found"
        assert "does not exist" in result.error
        assert "nonexistent" in result.error

    @pytest.mark.anyio
    async def test_collection_remove_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """Reject when no session exists."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        await remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionRemoveArgs(name="backend")
        result = await internal_collection_remove(args)

        assert result.success is False
        assert result.error_type == "no_project"

    @pytest.mark.anyio
    async def test_collection_remove_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Verify configuration is automatically saved."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="Backend")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionRemoveArgs(name="backend")
        result = await internal_collection_remove(args)

        assert result.success is True

        # Verify collection removed (cache updated by update_config)
        project = await session.get_project()
        assert len(project.collections) == 0

    @pytest.mark.anyio
    async def test_collection_remove_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, internal_collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="Backend")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        # Mock update_config to raise an exception
        update_mock = AsyncMock(side_effect=Exception("Disk full"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CollectionRemoveArgs(name="backend")
        result = await internal_collection_remove(args)

        assert result.success is False
        assert result.error_type == "save_error"
        assert "Failed to save project configuration" in result.error


class TestCollectionChange:
    """Tests for collection_change tool."""

    @pytest.mark.anyio
    async def test_change_collection_name_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change collection name only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = {"name": "backend", "categories": ["api"], "description": "Backend code"}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="backend-api")
        result = await internal_collection_change(args)

        assert result.success is True
        assert "renamed" in result.value
        assert "backend" in result.value
        assert "backend-api" in result.value

        project = await session.get_project()
        assert len(project.collections) == 1
        assert "backend-api" in project.collections
        assert project.collections[list(project.collections.keys())[0]].categories == ["api"]
        assert project.collections[list(project.collections.keys())[0]].description == "Backend code"

    @pytest.mark.anyio
    async def test_change_collection_description_only(self, test_session_with_data: Session) -> None:
        """Change collection description only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        project.collections["backend"] = Collection(categories=["api"], description="Old desc")
        await session.save_project(project)

        args = CollectionChangeArgs(name="backend", new_description="New desc")
        result = await internal_collection_change(args)

        assert result.success is True
        assert "updated successfully" in result.value

        project = await session.get_project()
        assert "backend" in project.collections
        assert project.collections["backend"].description == "New desc"
        assert project.collections["backend"].categories == ["api"]

    @pytest.mark.anyio
    async def test_change_collection_clear_description(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Clear description with empty string."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="Some desc")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_description="")
        result = await internal_collection_change(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].description is None

    @pytest.mark.anyio
    async def test_change_collection_categories_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change categories only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = {"name": "backend", "categories": ["api"], "description": "Backend"}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["api", "tests"])
        result = await internal_collection_change(args)

        if not result.success:
            print(f"Error: {result.error}")
        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests"]
        assert "backend" in project.collections
        assert project.collections[list(project.collections.keys())[0]].description == "Backend"

    @pytest.mark.anyio
    async def test_change_collection_deduplicates_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Deduplicate categories while preserving order."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = Collection(categories=[], description=None)
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["api", "tests", "api", "docs", "tests"])
        result = await internal_collection_change(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests", "docs"]

    @pytest.mark.anyio
    async def test_change_collection_multiple_fields(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change multiple fields together."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat))

        backend_collection = Collection(categories=[], description="Old")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(
            name="backend", new_name="backend-api", new_description="New", new_categories=["api"]
        )
        result = await internal_collection_change(args)

        assert result.success is True
        assert "renamed" in result.value

        project = await session.get_project()
        assert len(project.collections) == 1
        assert "backend-api" in project.collections
        assert project.collections[list(project.collections.keys())[0]].description == "New"
        assert project.collections[list(project.collections.keys())[0]].categories == ["api"]

    @pytest.mark.anyio
    async def test_change_collection_no_changes(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject when no changes provided."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "at least one change" in result.error.lower()

    @pytest.mark.anyio
    async def test_change_collection_nonexistent(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject changing non-existent collection."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionChangeArgs(name="nonexistent", new_name="new")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "not_found"
        assert "does not exist" in result.error

    @pytest.mark.anyio
    async def test_change_collection_duplicate_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject renaming to existing collection name."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="")
        frontend_collection = Collection(categories=[], description="")
        await session.update_config(
            lambda p: p.with_collection("backend", backend_collection).with_collection("frontend", frontend_collection)
        )

        args = CollectionChangeArgs(name="backend", new_name="frontend")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "already exists" in result.error

    @pytest.mark.anyio
    async def test_change_collection_invalid_new_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject invalid new_name that fails Collection validation."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description=None)
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "name" in result.error.lower()

    @pytest.mark.anyio
    async def test_change_collection_underscore_prefix_rejected(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject renaming collection to underscore-prefixed name."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description=None)
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="_reserved")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "underscore" in result.error.lower()

    @pytest.mark.anyio
    async def test_change_collection_invalid_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject non-existent categories."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["nonexistent"])
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "does not exist" in result.error

    @pytest.mark.anyio
    async def test_change_collection_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """Reject when no session exists."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        await remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionChangeArgs(name="backend", new_name="new")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "no_project"

    @pytest.mark.anyio
    async def test_change_collection_save_failure(
        self, test_session_with_data: Session, monkeypatch: MonkeyPatch
    ) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        project.collections["backend"] = Collection(categories=[], description=None)
        await session.save_project(project)

        underlying_message = "Disk full"
        update_mock = AsyncMock(side_effect=Exception(underlying_message))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CollectionChangeArgs(name="backend", new_name="new")
        result = await internal_collection_change(args)

        assert result.success is False
        assert result.error_type == "save_error"
        assert "Failed to save" in result.error
        assert underlying_message in result.error

    @pytest.mark.anyio
    async def test_change_collection_same_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Allow renaming to same name (no-op)."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description="")
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="backend")
        result = await internal_collection_change(args)

        assert result.success is True

    @pytest.mark.anyio
    async def test_change_collection_empty_categories(self, test_session_with_data: Session) -> None:
        """Allow changing to empty categories list."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, internal_collection_change

        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        project.collections["backend"] = Collection(categories=["api"], description="")
        await session.save_project(project)

        args = CollectionChangeArgs(name="backend", new_categories=[])
        result = await internal_collection_change(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == []


class TestCollectionUpdate:
    """Tests for collection_update tool."""

    @pytest.mark.anyio
    async def test_update_collection_add_single_category(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Add single category to collection."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        # Create categories using dict format
        await session.update_config(
            lambda p: p.with_category("api", Category(dir="api", patterns=["*.py"])).with_category(
                "tests", Category(dir="tests", patterns=["test_*.py"])
            )
        )

        # Create collection using dict format
        await session.update_config(
            lambda p: p.with_collection("backend", Collection(categories=["api"], description=None))
        )

        args = CollectionUpdateArgs(name="backend", add_categories=["tests"])
        result = await internal_collection_update(args)

        assert result.success is True
        assert "updated successfully" in result.value

        project = await session.get_project()
        assert project.collections["backend"].categories == ["api", "tests"]

    @pytest.mark.anyio
    async def test_update_collection_remove_single_category(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Remove single category from collection."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat))

        backend_collection = {"name": "backend", "categories": ["api", "tests"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", remove_categories=["tests"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api"]

    @pytest.mark.anyio
    async def test_update_collection_remove_nonexistent_idempotent(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Remove non-existent category is idempotent."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat))

        backend_collection = {"name": "backend", "categories": ["api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", remove_categories=["tests"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api"]

    @pytest.mark.anyio
    async def test_update_collection_add_and_remove(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Add and remove categories together."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = {"name": "backend", "categories": ["api", "tests"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", remove_categories=["tests"], add_categories=["docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "docs"]

    @pytest.mark.anyio
    async def test_update_collection_add_and_remove_same_category(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Same category in both add and remove results in it being present (remove then add)."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat))

        backend_collection = {"name": "backend", "categories": ["api", "tests"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        # Remove "tests" then add "tests" - should result in "tests" being present
        args = CollectionUpdateArgs(name="backend", remove_categories=["tests"], add_categories=["tests"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests"]

    @pytest.mark.anyio
    async def test_update_collection_add_multiple_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Add multiple categories."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = {"name": "backend", "categories": ["api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", add_categories=["tests", "docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests", "docs"]

    @pytest.mark.anyio
    async def test_update_collection_remove_multiple_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Remove multiple categories."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = {"name": "backend", "categories": ["api", "tests", "docs"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", remove_categories=["tests", "docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api"]

    @pytest.mark.anyio
    async def test_update_collection_deduplicates_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Deduplicate categories after operations."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        # Start with duplicates
        backend_collection = {"name": "backend", "categories": ["api", "tests", "api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", add_categories=["docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests", "docs"]

    @pytest.mark.anyio
    async def test_update_collection_skip_adding_duplicate(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Skip adding duplicate category."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["test_*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(
            lambda p: p.with_category("api", api_cat).with_category("tests", tests_cat).with_category("docs", docs_cat)
        )

        backend_collection = {"name": "backend", "categories": ["api", "tests"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", add_categories=["api", "docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "tests", "docs"]

    @pytest.mark.anyio
    async def test_update_collection_deduplicates_add_categories_argument(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Input add_categories argument with duplicates is deduplicated."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        docs_cat = Category(dir="docs", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category("api", api_cat).with_category("docs", docs_cat))

        backend_collection = {"name": "backend", "categories": ["api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        # Pass duplicates in add_categories
        args = CollectionUpdateArgs(name="backend", add_categories=["api", "api", "docs"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        # "api" should not be duplicated, "docs" should be added exactly once
        assert project.collections[list(project.collections.keys())[0]].categories.count("api") == 1
        assert project.collections[list(project.collections.keys())[0]].categories.count("docs") == 1
        assert project.collections[list(project.collections.keys())[0]].categories == ["api", "docs"]

    @pytest.mark.anyio
    async def test_update_collection_not_found(self, test_session_with_data: Session) -> None:
        """Reject non-existent collection."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        session = await get_session()
        project = await session.get_project()
        project.collections.clear()
        await session.save_project(project)

        args = CollectionUpdateArgs(name="backend", add_categories=["api"])
        result = await internal_collection_update(args)

        assert result.success is False
        assert result.error_type == "not_found"

    @pytest.mark.anyio
    async def test_update_collection_no_operations(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject when no operations provided."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = {"name": "backend", "categories": ["api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend")
        result = await internal_collection_update(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        # Check that validation errors are present
        assert "validation error" in result.error.lower()

    @pytest.mark.anyio
    async def test_update_collection_invalid_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject non-existent categories."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(categories=[], description=None)
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", add_categories=["nonexistent"])
        result = await internal_collection_update(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "does not exist" in result.error

    @pytest.mark.anyio
    async def test_update_collection_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """Reject when no session exists."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        await remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionUpdateArgs(name="backend", add_categories=["api"])
        result = await internal_collection_update(args)

        assert result.success is False
        assert result.error_type == "no_project"

    @pytest.mark.anyio
    async def test_update_collection_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat))

        backend_collection = Collection(categories=[], description=None)
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        underlying_message = "Disk full"
        update_mock = AsyncMock(side_effect=Exception(underlying_message))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CollectionUpdateArgs(name="backend", add_categories=["api"])
        result = await internal_collection_update(args)

        assert result.success is False
        assert result.error_type == "save_error"
        assert "Failed to save" in result.error
        assert underlying_message in result.error

    @pytest.mark.anyio
    async def test_update_collection_empty_result(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Allow empty categories result."""
        from mcp_guide.tools.tool_collection import CollectionUpdateArgs, internal_collection_update

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category("api", api_cat))

        backend_collection = {"name": "backend", "categories": ["api"], "description": None}
        await session.update_config(lambda p: p.with_collection("backend", backend_collection))

        args = CollectionUpdateArgs(name="backend", remove_categories=["api"])
        result = await internal_collection_update(args)

        assert result.success is True

        project = await session.get_project()
        assert project.collections[list(project.collections.keys())[0]].categories == []
