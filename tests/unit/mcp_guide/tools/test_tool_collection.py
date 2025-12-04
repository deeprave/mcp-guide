"""Tests for collection management tools."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Collection, Project
from mcp_guide.session import Session, set_current_session
from mcp_guide.tools.tool_collection import CollectionListArgs, collection_list


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
