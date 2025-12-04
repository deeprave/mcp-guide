"""Tests for collection management tools."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, set_current_session
from mcp_guide.tools.tool_collection import CollectionListArgs, collection_add, collection_list


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
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="backend")
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "backend" in result_dict["value"]
        assert "added successfully" in result_dict["value"]

        # Verify collection exists in project
        project = await session.get_project()
        assert len(project.collections) == 1
        assert project.collections[0].name == "backend"
        assert project.collections[0].categories == []
        assert project.collections[0].description == ""

    @pytest.mark.asyncio
    async def test_add_collection_with_description(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Create collection with name and description."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="docs", description="Documentation files")
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
        categories = [
            Category(name="api", dir="api", patterns=["*.py"]),
            Category(name="tests", dir="tests", patterns=["test_*.py"]),
        ]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=categories, collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="backend", categories=["api", "tests"])
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
        categories = [
            Category(name="api", dir="api", patterns=["*.py"]),
            Category(name="tests", dir="tests", patterns=["test_*.py"]),
            Category(name="docs", dir="docs", patterns=["*.md"]),
        ]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=categories, collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        # Pass duplicates: api, tests, api, docs, tests
        result_str = await collection_add(name="backend", categories=["api", "tests", "api", "docs", "tests"])
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        # Verify only unique categories stored, order preserved
        project = await session.get_project()
        assert project.collections[0].categories == ["api", "tests", "docs"]

    @pytest.mark.asyncio
    async def test_add_collection_duplicate_name_error(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Duplicate collection name should return validation error."""
        existing = Collection(name="backend", categories=[], description="")
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[existing])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="backend")
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "already exists" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_add_collection_invalid_description_too_long(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Description exceeding max length should return validation error."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        long_desc = "x" * 501
        result_str = await collection_add(name="backend", description=long_desc)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "exceeds" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_add_collection_invalid_description_quotes(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Description with quotes should return validation error."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="backend", description='Has "quotes" in it')
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "quote" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_add_collection_nonexistent_categories(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Non-existent categories should return validation error."""
        categories = [Category(name="api", dir="api", patterns=["*.py"])]
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=categories, collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        result_str = await collection_add(name="backend", categories=["api", "nonexistent"])
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "does not exist" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_add_collection_no_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session should return error."""
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        result_str = await collection_add(name="backend")
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_add_collection_invalid_name(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Invalid collection name should return validation error."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)
        monkeypatch.setenv("PWD", "/fake/path/test")

        # Test name too long
        result_str = await collection_add(name="x" * 31)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
