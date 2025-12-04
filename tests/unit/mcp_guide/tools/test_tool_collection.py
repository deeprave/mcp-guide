"""Tests for collection management tools."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, get_or_create_session, set_current_session
from mcp_guide.tools.tool_collection import CollectionAddArgs, CollectionListArgs, collection_add, collection_list


class TestCollectionList:
    """Tests for collection_list tool."""

    @pytest.mark.asyncio
    async def test_verbose_true_returns_full_details(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """verbose=True should return full collection details."""
        collections = [
            Collection(name="backend", categories=["api", "tests"], description="Backend code"),
            Collection(name="documentation", categories=["docs"], description="All docs"),
            Collection(name="empty", categories=[], description="Empty collection"),
        ]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=collections)
        set_current_session(session)

        # Set PWD so get_or_create_session can determine project name
        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionListArgs(verbose=True)
        result_str = await collection_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(result_dict["value"]) == 3
        assert result_dict["value"][0] == {
            "name": "backend",
            "categories": ["api", "tests"],
            "description": "Backend code",
        }
        assert result_dict["value"][1] == {
            "name": "documentation",
            "categories": ["docs"],
            "description": "All docs",
        }
        assert result_dict["value"][2] == {
            "name": "empty",
            "categories": [],
            "description": "Empty collection",
        }

    @pytest.mark.asyncio
    async def test_verbose_false_returns_names_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """verbose=False should return just collection names."""
        collections = [
            Collection(name="backend", categories=["api"], description="Backend"),
            Collection(name="docs", categories=["md"], description="Docs"),
        ]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=collections)
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionListArgs(verbose=False)
        result_str = await collection_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert result_dict["value"] == ["backend", "docs"]

    @pytest.mark.asyncio
    async def test_empty_collections_returns_empty_list(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Empty collections list should return empty list."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionListArgs()
        result_str = await collection_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert result_dict["value"] == []

    @pytest.mark.asyncio
    async def test_collection_with_empty_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Collection with empty categories list should return empty list in categories field."""
        collections = [Collection(name="empty", categories=[], description="No categories")]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=collections)
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        args = CollectionListArgs(verbose=True)
        result_str = await collection_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(result_dict["value"]) == 1
        assert result_dict["value"][0]["categories"] == []

    @pytest.mark.asyncio
    async def test_no_active_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        # Unset PWD and CWD so get_or_create_session fails
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionListArgs()
        result_str = await collection_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"


class TestCollectionAdd:
    """Tests for collection_add tool."""

    @pytest.mark.asyncio
    async def test_add_collection_name_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with just name."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        # Initialize project via proper API
        await session.update_config(lambda p: p)

        args = CollectionAddArgs(name="backend")
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "backend" in result_dict["value"]
        assert "added successfully" in result_dict["value"]

        # Verify collection exists in project
        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "backend"
        assert project.collections[0].categories == []
        assert project.collections[0].description is None

    @pytest.mark.asyncio
    async def test_add_collection_with_description(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with name and description."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionAddArgs(name="docs", description="Documentation files")
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        # Verify description is set
        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "docs"
        assert project.collections[0].description == "Documentation files"

    @pytest.mark.asyncio
    async def test_add_collection_with_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with valid categories."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        # Add categories via proper API
        await session.update_config(
            lambda p: p.with_category(Category(name="api", dir="api", patterns=["*.py"])).with_category(
                Category(name="tests", dir="tests", patterns=["test_*.py"])
            )
        )

        args = CollectionAddArgs(name="backend", categories=["api", "tests"])
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        # Verify categories are set
        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "backend"
        assert project.collections[0].categories == ["api", "tests"]

    @pytest.mark.asyncio
    async def test_add_collection_deduplicates_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Duplicate categories should be deduplicated while preserving order."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        # Add categories via proper API
        await session.update_config(
            lambda p: p.with_category(Category(name="api", dir="api", patterns=["*.py"]))
            .with_category(Category(name="tests", dir="tests", patterns=["test_*.py"]))
            .with_category(Category(name="docs", dir="docs", patterns=["*.md"]))
        )

        # Pass duplicates: api, tests, api, docs, tests
        args = CollectionAddArgs(name="backend", categories=["api", "tests", "api", "docs", "tests"])
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        # Verify only unique categories stored, order preserved
        project = await session.get_project()
        assert project.collections[0].categories == ["api", "tests", "docs"]

    @pytest.mark.asyncio
    async def test_add_collection_duplicate_name_error(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Duplicate collection name should return validation error."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        # Add existing collection via proper API
        await session.update_config(
            lambda p: p.with_collection(Collection(name="backend", categories=[], description=""))
        )

        # Capture original project state
        original_project = await session.get_project()
        original_collections = list(original_project.collections)

        args = CollectionAddArgs(name="backend")
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "already exists" in result_dict["error"]

        # Project state should be unchanged after failed validation
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)
        assert project.collections == original_collections

    @pytest.mark.asyncio
    async def test_add_collection_invalid_description_too_long(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Description exceeding max length should return validation error."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        # Capture original project state
        original_project = await session.get_project()
        original_collections = list(original_project.collections)

        long_desc = "x" * 501
        args = CollectionAddArgs(name="backend", description=long_desc)
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "exceeds" in result_dict["error"]

        # Project state should be unchanged
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.asyncio
    async def test_add_collection_invalid_description_quotes(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Description with quotes should return validation error."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionAddArgs(name="backend", description='Has "quotes" in it')
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "quote" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_add_collection_nonexistent_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Non-existent categories should return validation error."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        # Add one category via proper API
        await session.update_config(lambda p: p.with_category(Category(name="api", dir="api", patterns=["*.py"])))

        # Capture original project state
        original_project = await session.get_project()
        original_collections = list(original_project.collections)

        args = CollectionAddArgs(name="backend", categories=["api", "nonexistent"])
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "does not exist" in result_dict["error"]

        # Project state should be unchanged
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.asyncio
    async def test_add_collection_no_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session should return error."""
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionAddArgs(name="backend")
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_add_collection_invalid_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Invalid collection name should return validation error."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        # Capture original project state
        original_project = await session.get_project()
        original_collections = list(original_project.collections)

        # Test name too long
        args = CollectionAddArgs(name="x" * 31)
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

        # Project state should be unchanged
        project = await session.get_project()
        assert len(project.collections) == len(original_collections)

    @pytest.mark.asyncio
    async def test_add_collection_save_error(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Configuration save failure should return ERROR_SAVE."""
        from mcp_guide.session import get_or_create_session

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        # Mock update_config to raise an exception
        async def mock_update_config(*args, **kwargs):  # type: ignore
            raise RuntimeError("Simulated save failure")

        monkeypatch.setattr(session, "update_config", mock_update_config)

        args = CollectionAddArgs(name="backend")
        result_str = await collection_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "save_error"
        assert "Failed to save" in result_dict["error"]


class TestCollectionRemove:
    """Tests for collection_remove tool."""

    @pytest.mark.asyncio
    async def test_collection_remove_existing(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Remove existing collection."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=["api"], description="Backend")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionRemoveArgs(name="backend")
        result_str = await collection_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "removed successfully" in result_dict["value"]

        project = await session.get_project()
        assert len(project.collections) == 0

    @pytest.mark.asyncio
    async def test_collection_remove_nonexistent(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject removing non-existent collection."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionRemoveArgs(name="nonexistent")
        result_str = await collection_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]
        assert "nonexistent" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_collection_remove_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """Reject when no session exists."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, collection_remove

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionRemoveArgs(name="backend")
        result_str = await collection_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_collection_remove_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Verify configuration is automatically saved."""
        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="Backend")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionRemoveArgs(name="backend")
        result_str = await collection_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        # Verify collection removed (cache updated by update_config)
        project = await session.get_project()
        assert len(project.collections) == 0

    @pytest.mark.asyncio
    async def test_collection_remove_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_collection import CollectionRemoveArgs, collection_remove

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="Backend")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        # Mock update_config to raise an exception
        update_mock = AsyncMock(side_effect=Exception("Disk full"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CollectionRemoveArgs(name="backend")
        result_str = await collection_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "save_error"
        assert "Failed to save project configuration" in result_dict["error"]


class TestCollectionChange:
    """Tests for collection_change tool."""

    @pytest.mark.asyncio
    async def test_change_collection_name_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change collection name only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=["api"], description="Backend code")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="backend-api")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "renamed" in result_dict["value"]
        assert "backend" in result_dict["value"]
        assert "backend-api" in result_dict["value"]

        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "backend-api"
        assert project.collections[0].categories == ["api"]
        assert project.collections[0].description == "Backend code"

    @pytest.mark.asyncio
    async def test_change_collection_description_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change collection description only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=["api"], description="Old desc")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_description="New desc")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "updated successfully" in result_dict["value"]

        project = await session.get_project()
        assert project.collections[0].name == "backend"
        assert project.collections[0].description == "New desc"
        assert project.collections[0].categories == ["api"]

    @pytest.mark.asyncio
    async def test_change_collection_clear_description(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Clear description with empty string."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="Some desc")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_description="")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        project = await session.get_project()
        assert project.collections[0].description is None

    @pytest.mark.asyncio
    async def test_change_collection_categories_only(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change categories only."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        tests_cat = Category(name="tests", dir="tests", patterns=["test_*.py"])
        docs_cat = Category(name="docs", dir="docs", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category(api_cat).with_category(tests_cat).with_category(docs_cat))

        backend_collection = Collection(name="backend", categories=["api"], description="Backend")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["api", "tests"])
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        project = await session.get_project()
        assert project.collections[0].categories == ["api", "tests"]
        assert project.collections[0].name == "backend"
        assert project.collections[0].description == "Backend"

    @pytest.mark.asyncio
    async def test_change_collection_deduplicates_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Deduplicate categories while preserving order."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category(api_cat))

        backend_collection = Collection(name="backend", categories=[], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["api", "api", "api"])
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        project = await session.get_project()
        assert project.collections[0].categories == ["api"]

    @pytest.mark.asyncio
    async def test_change_collection_multiple_fields(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Change multiple fields together."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category(api_cat))

        backend_collection = Collection(name="backend", categories=[], description="Old")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(
            name="backend", new_name="backend-api", new_description="New", new_categories=["api"]
        )
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "renamed" in result_dict["value"]

        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "backend-api"
        assert project.collections[0].description == "New"
        assert project.collections[0].categories == ["api"]

    @pytest.mark.asyncio
    async def test_change_collection_no_changes(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject when no changes provided."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "at least one change" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_change_collection_nonexistent(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject changing non-existent collection."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
        await session.update_config(lambda p: p)

        args = CollectionChangeArgs(name="nonexistent", new_name="new")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_change_collection_duplicate_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject renaming to existing collection name."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="")
        frontend_collection = Collection(name="frontend", categories=[], description="")
        await session.update_config(
            lambda p: p.with_collection(backend_collection).with_collection(frontend_collection)
        )

        args = CollectionChangeArgs(name="backend", new_name="frontend")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "already exists" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_change_collection_invalid_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Reject non-existent categories."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=["nonexistent"])
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "does not exist" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_change_collection_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """Reject when no session exists."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CollectionChangeArgs(name="backend", new_name="new")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_change_collection_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        update_mock = AsyncMock(side_effect=Exception("Disk full"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CollectionChangeArgs(name="backend", new_name="new")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "save_error"
        assert "Failed to save" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_change_collection_same_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Allow renaming to same name (no-op)."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        backend_collection = Collection(name="backend", categories=[], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_name="backend")
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

    @pytest.mark.asyncio
    async def test_change_collection_empty_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Allow changing to empty categories list."""
        from mcp_guide.tools.tool_collection import CollectionChangeArgs, collection_change

        monkeypatch.setenv("PWD", "/fake/path/test")
        session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))

        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        await session.update_config(lambda p: p.with_category(api_cat))

        backend_collection = Collection(name="backend", categories=["api"], description="")
        await session.update_config(lambda p: p.with_collection(backend_collection))

        args = CollectionChangeArgs(name="backend", new_categories=[])
        result_str = await collection_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        project = await session.get_project()
        assert project.collections[0].categories == []
