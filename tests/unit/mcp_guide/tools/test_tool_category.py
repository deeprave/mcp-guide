"""Tests for category management tools."""

import json
import os
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, set_current_session
from mcp_guide.tools.tool_category import CategoryListArgs, category_list


class TestCategoryList:
    """Tests for category_list tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

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

        # Unset PWD and CWD so get_or_create_session fails
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

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
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

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
    async def test_category_add_dir_defaults_to_name(self, tmp_path: Path) -> None:
        """When dir is omitted, it defaults to name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        # Omit dir parameter
        args = CategoryAddArgs(name="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        # Verify dir defaulted to name
        assert session._cached_project.categories[0].dir == "docs"
        assert session._cached_project.categories[0].name == "docs"

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

    @pytest.mark.asyncio
    async def test_category_add_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(**args.model_dump())
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


class TestCategoryRemove:
    """Tests for category_remove tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

    @pytest.mark.asyncio
    async def test_category_remove_existing(self, tmp_path: Path) -> None:
        """Remove existing category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_category = Category(name="docs", dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories=[docs_category], collections=[])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "removed successfully" in result_dict["value"]
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_nonexistent(self, tmp_path: Path) -> None:
        """Reject removing non-existent category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories=[], collections=[])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_updates_single_collection(self, tmp_path: Path) -> None:
        """Remove category from single collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_category = Category(name="docs", dir="docs", patterns=["*.md"])
        all_collection = Collection(name="all", categories=["docs"])
        session._cached_project = Project(name="test", categories=[docs_category], collections=[all_collection])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 0
        assert len(session._cached_project.collections) == 1
        assert session._cached_project.collections[0].categories == []

    @pytest.mark.asyncio
    async def test_category_remove_updates_multiple_collections(self, tmp_path: Path) -> None:
        """Remove category from multiple collections."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_cat = Category(name="docs", dir="docs", patterns=["*.md"])
        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        tests_cat = Category(name="tests", dir="tests", patterns=["*.py"])
        backend_col = Collection(name="backend", categories=["api", "tests"])
        frontend_col = Collection(name="frontend", categories=["docs", "api"])
        session._cached_project = Project(
            name="test", categories=[docs_cat, api_cat, tests_cat], collections=[backend_col, frontend_col]
        )
        set_current_session(session)

        args = CategoryRemoveArgs(name="api")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 2
        assert not any(c.name == "api" for c in session._cached_project.categories)
        backend = next(c for c in session._cached_project.collections if c.name == "backend")
        frontend = next(c for c in session._cached_project.collections if c.name == "frontend")
        assert backend.categories == ["tests"]
        assert frontend.categories == ["docs"]

    @pytest.mark.asyncio
    async def test_category_remove_not_in_collections(self, tmp_path: Path) -> None:
        """Remove category not in any collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_cat = Category(name="docs", dir="docs", patterns=["*.md"])
        api_cat = Category(name="api", dir="api", patterns=["*.py"])
        backend_col = Collection(name="backend", categories=["api"])
        session._cached_project = Project(name="test", categories=[docs_cat, api_cat], collections=[backend_col])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories[0].name == "api"
        assert session._cached_project.collections[0].categories == ["api"]

    @pytest.mark.asyncio
    async def test_category_remove_auto_saves(self, tmp_path: Path) -> None:
        """Verify category removal is persisted."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_category = Category(name="docs", dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories=[docs_category], collections=[])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        reloaded_project = await manager.get_or_create_project_config("test")
        assert len(reloaded_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_remove_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_category = Category(name="docs", dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories=[docs_category], collections=[])
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "save" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_category_remove_updates_timestamp(self, tmp_path: Path) -> None:
        """Verify updated_at timestamp changes after remove."""
        import asyncio

        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(config_manager=manager, project_name="test")
        docs_category = Category(name="docs", dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories=[docs_category], collections=[])
        set_current_session(session)

        original_time = session._cached_project.updated_at
        await asyncio.sleep(0.01)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(**args.model_dump())
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        new_time = session._cached_project.updated_at
        assert new_time > original_time
