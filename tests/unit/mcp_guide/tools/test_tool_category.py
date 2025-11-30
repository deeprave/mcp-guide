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


class TestCategoryAdd:
    """Tests for category_add tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        test_project_dir = tmp_path / "test"
        test_project_dir.mkdir(exist_ok=True)
        monkeypatch.setenv("PWD", str(test_project_dir))
        yield
        remove_current_session("test")

    @pytest.mark.asyncio
    async def test_category_add_minimal(self, tmp_path: Path) -> None:
        """Add category with minimal args."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "docs" in result_dict["value"]
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories[0].name == "docs"
        assert session._cached_project.categories[0].dir == "docs"
        assert session._cached_project.categories[0].patterns == ["*.md"]
        assert session._cached_project.categories[0].description is None

    @pytest.mark.asyncio
    async def test_category_add_with_description(self, tmp_path: Path) -> None:
        """Add category with all args."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="api", dir="api", patterns=["*.py"], description="API documentation")
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories[0].name == "api"
        assert session._cached_project.categories[0].description == "API documentation"

    @pytest.mark.asyncio
    async def test_category_add_multiple_patterns(self, tmp_path: Path) -> None:
        """Add category with multiple patterns."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="code", dir="src", patterns=["*.py", "*.pyx", "*.pyi"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert session._cached_project.categories[0].patterns == ["*.py", "*.pyx", "*.pyi"]

    @pytest.mark.asyncio
    async def test_category_add_duplicate_name(self, tmp_path: Path) -> None:
        """Reject duplicate category name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        existing = Category(name="docs", dir="documentation", patterns=["*.md"])
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[existing], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="other", patterns=["*.txt"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "already exists" in result_dict["error"].lower()
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories[0].dir == "documentation"

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_empty(self, tmp_path: Path) -> None:
        """Reject invalid name (empty)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_special_chars(self, tmp_path: Path) -> None:
        """Reject invalid name (special chars)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs/api", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_too_long(self, tmp_path: Path) -> None:
        """Reject invalid name (exceeds 30 characters)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="a" * 31, dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "30 characters" in result_dict["error"]
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_directory_absolute(self, tmp_path: Path) -> None:
        """Reject invalid directory (absolute path)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="/absolute/path", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_directory_traversal(self, tmp_path: Path) -> None:
        """Reject invalid directory (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="../parent", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_too_long(self, tmp_path: Path) -> None:
        """Reject invalid description (too long)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description="x" * 501)
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_quotes(self, tmp_path: Path) -> None:
        """Reject invalid description (quotes)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description='Has "quotes"')
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_absolute(self, tmp_path: Path) -> None:
        """Reject invalid pattern (absolute path)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["/absolute/*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_traversal(self, tmp_path: Path) -> None:
        """Reject invalid pattern (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["../*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_empty_patterns(self, tmp_path: Path) -> None:
        """Allow empty patterns list."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=[])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories[0].patterns == []

    @pytest.mark.asyncio
    async def test_category_add_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Auto-save after successful add."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        update_mock = AsyncMock()
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        update_mock.assert_called_once()

    def test_category_add_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        import asyncio

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        monkeypatch.delenv("PWD", raising=False)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = asyncio.run(category_add(**args.model_dump()))
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_add_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "save" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_category_add_updates_timestamp(self, tmp_path: Path) -> None:
        """Verify updated_at timestamp changes after add."""
        import asyncio

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        original_time = session._cached_project.updated_at
        await asyncio.sleep(0.01)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        new_time = session._cached_project.updated_at
        assert new_time > original_time
