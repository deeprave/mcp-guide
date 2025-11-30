"""Tests for category management tools."""

import json
import os
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Project
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_category import CategoryListArgs, category_list


class TestCategoryList:
    """Tests for category_list tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        # Mock PWD to match test project name
        test_project_dir = tmp_path / "test"
        test_project_dir.mkdir(exist_ok=True)
        monkeypatch.setenv("PWD", str(test_project_dir))
        yield
        remove_current_session("test")

    @pytest.mark.asyncio
    async def test_list_empty_categories(self, tmp_path: Path) -> None:
        """List empty categories returns empty list."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert result_dict["value"] == []

    @pytest.mark.asyncio
    async def test_list_single_category(self, tmp_path: Path) -> None:
        """List single category returns all fields."""
        category = Category(
            name="docs",
            dir="documentation",
            patterns=["*.md", "*.txt"],
        )
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[category], collections=[])
        set_current_session(session)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(result_dict["value"]) == 1
        assert result_dict["value"][0]["name"] == "docs"
        assert result_dict["value"][0]["dir"] == "documentation"
        assert result_dict["value"][0]["patterns"] == ["*.md", "*.txt"]
        assert result_dict["value"][0]["description"] is None

    @pytest.mark.asyncio
    async def test_list_multiple_categories(self, tmp_path: Path) -> None:
        """List multiple categories returns all."""
        cat1 = Category(name="docs", dir="docs", patterns=["*.md"])
        cat2 = Category(name="src", dir="src", patterns=["*.py"])
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[cat1, cat2], collections=[])
        set_current_session(session)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(result_dict["value"]) == 2
        assert result_dict["value"][0]["name"] == "docs"
        assert result_dict["value"][1]["name"] == "src"

    def test_no_active_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        import asyncio

        # Unset PWD so get_or_create_session fails
        monkeypatch.delenv("PWD", raising=False)

        args = CategoryListArgs()
        result_str = asyncio.run(category_list(args))
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_result_pattern_response(self, tmp_path: Path) -> None:
        """Returns Result.ok with proper structure."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert isinstance(result_dict["value"], list)
