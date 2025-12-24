"""Tests for category management tools."""

import json
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category, Collection, Project
from mcp_guide.session import Session, set_current_session
from mcp_guide.tools.tool_category import CategoryListArgs, CategoryListFilesArgs, category_list, category_list_files


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
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
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
            dir="documentation",
            patterns=["*.md", "*.txt"],
        )
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={"docs": category}, collections={})
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
        cat1 = Category(dir="docs", patterns=["*.md"])
        cat2 = Category(dir="src", patterns=["*.py"])
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={"docs": cat1, "src": cat2}, collections={})
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
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
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
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "docs" in result_dict["value"]
        assert len(session._cached_project.categories) == 1
        assert "docs" in session._cached_project.categories
        assert session._cached_project.categories["docs"].dir == "docs"
        assert session._cached_project.categories["docs"].patterns == ["*.md"]
        assert session._cached_project.categories["docs"].description is None

    @pytest.mark.asyncio
    async def test_category_add_with_description(self, tmp_path: Path) -> None:
        """Add category with all args."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="api", dir="api", patterns=["*.py"], description="API documentation")
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert "api" in session._cached_project.categories
        assert session._cached_project.categories["api"].description == "API documentation"

    @pytest.mark.asyncio
    async def test_category_add_dir_defaults_to_name(self, tmp_path: Path) -> None:
        """When dir is omitted, it defaults to name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        # Omit dir parameter
        args = CategoryAddArgs(name="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        # Verify dir defaulted to name
        assert session._cached_project.categories["docs"].dir == "docs"
        assert "docs" in session._cached_project.categories

    @pytest.mark.asyncio
    async def test_category_add_multiple_patterns(self, tmp_path: Path) -> None:
        """Add category with multiple patterns."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="code", dir="src", patterns=["*.py", "*.pyx", "*.pyi"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert session._cached_project.categories["code"].patterns == ["*.py", "*.pyx", "*.pyi"]

    @pytest.mark.asyncio
    async def test_category_add_duplicate_name(self, tmp_path: Path) -> None:
        """Reject duplicate category name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        existing = Category(dir="documentation", patterns=["*.md"])
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={"docs": existing}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="other", patterns=["*.txt"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "already exists" in result_dict["error"].lower()
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories["docs"].dir == "documentation"

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_empty(self, tmp_path: Path) -> None:
        """Reject invalid name (empty)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_special_chars(self, tmp_path: Path) -> None:
        """Reject invalid name (special chars)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs/api", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_too_long(self, tmp_path: Path) -> None:
        """Reject invalid name (exceeds 30 characters)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="a" * 31, dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
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
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="/absolute/path", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_directory_traversal(self, tmp_path: Path) -> None:
        """Reject invalid directory (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="../parent", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_too_long(self, tmp_path: Path) -> None:
        """Reject invalid description (too long)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description="x" * 501)
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_quotes(self, tmp_path: Path) -> None:
        """Reject invalid description (quotes)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description='Has "quotes"')
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_absolute(self, tmp_path: Path) -> None:
        """Reject invalid pattern (absolute path)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["/absolute/*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_traversal(self, tmp_path: Path) -> None:
        """Reject invalid pattern (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["../*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_empty_patterns(self, tmp_path: Path) -> None:
        """Allow empty patterns list."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=[])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert session._cached_project.categories["docs"].patterns == []

    @pytest.mark.asyncio
    async def test_category_add_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Auto-save after successful add."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        update_mock = AsyncMock()
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
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
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_add_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "save" in result_dict["error"].lower()


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
        session = Session(_config_manager=manager, project_name="test")
        docs_category = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_category}, collections={})
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "removed successfully" in result_dict["value"]
        assert len(session._cached_project.categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_nonexistent(self, tmp_path: Path) -> None:
        """Reject removing non-existent category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
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
        session = Session(_config_manager=manager, project_name="test")
        docs_category = Category(dir="docs", patterns=["*.md"])
        all_collection = Collection(categories=["docs"])
        session._cached_project = Project(
            name="test", categories={"docs": docs_category}, collections={"all": all_collection}
        )
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 0
        assert len(session._cached_project.collections) == 1
        assert session._cached_project.collections["all"].categories == []

    @pytest.mark.asyncio
    async def test_category_remove_updates_multiple_collections(self, tmp_path: Path) -> None:
        """Remove category from multiple collections."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        tests_cat = Category(dir="tests", patterns=["*.py"])
        backend_col = Collection(categories=["api", "tests"])
        frontend_col = Collection(categories=["docs", "api"])
        session._cached_project = Project(
            name="test",
            categories={"docs": docs_cat, "api": api_cat, "tests": tests_cat},
            collections={"backend": backend_col, "frontend": frontend_col},
        )
        set_current_session(session)

        args = CategoryRemoveArgs(name="api")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 2
        assert "api" not in session._cached_project.categories
        assert session._cached_project.collections["backend"].categories == ["tests"]
        assert session._cached_project.collections["frontend"].categories == ["docs"]

    @pytest.mark.asyncio
    async def test_category_remove_not_in_collections(self, tmp_path: Path) -> None:
        """Remove category not in any collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        backend_col = Collection(categories=["api"])
        session._cached_project = Project(
            name="test", categories={"docs": docs_cat, "api": api_cat}, collections={"backend": backend_col}
        )
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(session._cached_project.categories) == 1
        assert "api" in session._cached_project.categories
        assert session._cached_project.collections["backend"].categories == ["api"]

    @pytest.mark.asyncio
    async def test_category_remove_auto_saves(self, tmp_path: Path) -> None:
        """Verify category removal is persisted."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_category = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_category}, collections={})
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
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
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_remove_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_category = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_category}, collections={})
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "save" in result_dict["error"].lower()


class TestCategoryChange:
    """Tests for category_change tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

    @pytest.mark.asyncio
    async def test_category_change_name(self, tmp_path: Path) -> None:
        """Change category name (rename)."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"], description="Documentation")
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "docs" not in session._cached_project.categories
        doc_cat = session._cached_project.categories["documentation"]
        assert doc_cat.dir == "docs"
        assert doc_cat.patterns == ["*.md"]
        assert doc_cat.description == "Documentation"

    @pytest.mark.asyncio
    async def test_category_change_dir(self, tmp_path: Path) -> None:
        """Change category directory."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_dir="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.dir == "documentation"
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_change_description(self, tmp_path: Path) -> None:
        """Change category description."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"], description="Old")
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="New description")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.description == "New description"
        assert doc_cat.dir == "docs"

    @pytest.mark.asyncio
    async def test_category_change_clear_description(self, tmp_path: Path) -> None:
        """Clear category description with empty string."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"], description="Something")
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.description is None

    @pytest.mark.asyncio
    async def test_category_change_patterns(self, tmp_path: Path) -> None:
        """Replace category patterns."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_patterns=["*.txt", "*.rst"])
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.txt", "*.rst"]

    @pytest.mark.asyncio
    async def test_category_change_multiple_fields(self, tmp_path: Path) -> None:
        """Change multiple fields at once."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation", new_dir="docs_new", new_description="Updated")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["documentation"]
        assert doc_cat.dir == "docs_new"
        assert doc_cat.description == "Updated"

    @pytest.mark.asyncio
    async def test_category_change_name_to_same_name(self, tmp_path: Path) -> None:
        """Renaming to same name should succeed without updating collections."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        all_col = Collection(categories=["docs", "api"])
        session._cached_project = Project(
            name="test", categories={"docs": docs_cat, "api": api_cat}, collections={"all": all_col}
        )
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="docs")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "updated successfully" in result_dict["value"]
        all_collection = session._cached_project.collections["all"]
        assert all_collection.categories == ["docs", "api"]

    @pytest.mark.asyncio
    async def test_category_change_name_updates_collections(self, tmp_path: Path) -> None:
        """Rename updates collections."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        all_col = Collection(categories=["docs", "api"])
        session._cached_project = Project(
            name="test", categories={"docs": docs_cat, "api": api_cat}, collections={"all": all_col}
        )
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        all_collection = session._cached_project.collections["all"]
        assert all_collection.categories == ["documentation", "api"]

    @pytest.mark.asyncio
    async def test_category_change_name_updates_multiple_collections(self, tmp_path: Path) -> None:
        """Rename updates multiple collections."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        backend_col = Collection(categories=["api"])
        frontend_col = Collection(categories=["docs", "api"])
        session._cached_project = Project(
            name="test",
            categories={"docs": docs_cat, "api": api_cat},
            collections={"backend": backend_col, "frontend": frontend_col},
        )
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        backend = session._cached_project.collections["backend"]
        frontend = session._cached_project.collections["frontend"]
        assert backend.categories == ["api"]
        assert frontend.categories == ["documentation", "api"]

    @pytest.mark.asyncio
    async def test_category_change_not_found(self, tmp_path: Path) -> None:
        """Reject changing non-existent category."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_category_change_name_conflict(self, tmp_path: Path) -> None:
        """Reject new name that conflicts with existing category."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        api_cat = Category(dir="api", patterns=["*.py"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat, "api": api_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="api")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "already exists" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_category_change_invalid_name(self, tmp_path: Path) -> None:
        """Reject invalid new name."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="invalid name!")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_category_change_empty_dir(self, tmp_path: Path) -> None:
        """Reject empty string for new directory."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_dir="")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "cannot be empty" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_category_change_invalid_dir(self, tmp_path: Path) -> None:
        """Reject invalid new directory."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_dir="/absolute/path")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_category_change_invalid_description(self, tmp_path: Path) -> None:
        """Reject invalid new description."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description='Has "quotes"')
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_category_change_invalid_pattern(self, tmp_path: Path) -> None:
        """Reject invalid new pattern."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_patterns=["../traversal"])
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_category_change_no_changes(self, tmp_path: Path) -> None:
        """Reject when no changes provided."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "at least one change" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_category_change_auto_saves(self, tmp_path: Path) -> None:
        """Verify changes are persisted."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="Updated")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        reloaded_project = await manager.get_or_create_project_config("test")
        doc_cat = reloaded_project.categories["docs"]
        assert doc_cat.description == "Updated"

    @pytest.mark.asyncio
    async def test_category_change_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CategoryChangeArgs(name="docs", new_description="Updated")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_change_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryChangeArgs(name="docs", new_description="Updated")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "save" in result_dict["error"].lower()


class TestCategoryUpdate:
    """Tests for category_update tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

    @pytest.mark.asyncio
    async def test_category_update_add_single_pattern(self, tmp_path: Path) -> None:
        """Add a single pattern to category."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md", "*.txt"]

    @pytest.mark.asyncio
    async def test_category_update_remove_single_pattern(self, tmp_path: Path) -> None:
        """Remove a single pattern from category."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md", "*.txt"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", remove_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_update_add_and_remove_patterns(self, tmp_path: Path) -> None:
        """Add and remove patterns together (remove happens first)."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md", "*.txt"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", remove_patterns=["*.txt"], add_patterns=["*.rst"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md", "*.rst"]

    @pytest.mark.asyncio
    async def test_category_update_remove_nonexistent_pattern(self, tmp_path: Path) -> None:
        """Remove non-existent pattern succeeds (idempotent)."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", remove_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_update_add_multiple_patterns(self, tmp_path: Path) -> None:
        """Add multiple patterns at once."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt", "*.rst"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md", "*.txt", "*.rst"]

    @pytest.mark.asyncio
    async def test_category_update_remove_multiple_patterns(self, tmp_path: Path) -> None:
        """Remove multiple patterns at once."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md", "*.txt", "*.rst"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", remove_patterns=["*.txt", "*.rst"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_update_invalid_add_pattern(self, tmp_path: Path) -> None:
        """Reject invalid pattern in add_patterns."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["../traversal"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_category_update_category_not_found(self, tmp_path: Path) -> None:
        """Reject update for non-existent category."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_category_update_no_operations(self, tmp_path: Path) -> None:
        """Reject when no operations provided."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs")
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "at least one" in result_dict["error"].lower()

    @pytest.mark.asyncio
    async def test_category_update_auto_saves(self, tmp_path: Path) -> None:
        """Verify changes are persisted."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True

        reloaded_project = await manager.get_or_create_project_config("test")
        doc_cat = reloaded_project.categories["docs"]
        assert doc_cat.patterns == ["*.md", "*.txt"]

    @pytest.mark.asyncio
    async def test_category_update_no_session(self, monkeypatch: MonkeyPatch) -> None:
        """No active session returns error."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_category_update_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.txt"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "save_error"

    @pytest.mark.asyncio
    async def test_category_update_add_duplicate_pattern(self, tmp_path: Path) -> None:
        """Adding duplicate pattern should not create duplicates."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        docs_cat = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.md"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_update_deduplicates_patterns(self, tmp_path: Path) -> None:
        """Deduplicate patterns after add/remove operations."""
        from mcp_guide.tools.tool_category import CategoryUpdateArgs, category_update

        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        # Start with existing duplicates in patterns
        docs_cat = Category(dir="docs", patterns=["*.py", "*.txt", "*.py"])
        session._cached_project = Project(name="test", categories={"docs": docs_cat}, collections={})
        set_current_session(session)

        args = CategoryUpdateArgs(name="docs", add_patterns=["*.md"])
        result_str = await category_update(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = session._cached_project.categories["docs"]
        # Should deduplicate existing duplicates
        assert doc_cat.patterns == ["*.py", "*.txt", "*.md"]


class TestCategoryListFiles:
    """Tests for category_list_files tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

    @pytest.mark.asyncio
    async def test_category_not_found(self, tmp_path: Path) -> None:
        """Test error when category doesn't exist."""
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        session._cached_project = Project(name="test", categories={}, collections={})
        set_current_session(session)

        args = CategoryListFilesArgs(name="nonexistent")
        result_str = await category_list_files(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "nonexistent" in result_dict["error"]

    @pytest.mark.asyncio
    async def test_no_session_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test error when no session is active."""
        # Unset PWD and CWD so get_or_create_session fails
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        args = CategoryListFilesArgs(name="docs")
        result_str = await category_list_files(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "no_project"

    @pytest.mark.asyncio
    async def test_empty_directory(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test success with empty directory."""
        # Setup session with category
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        category = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": category}, collections={})
        set_current_session(session)

        # Mock docroot to point to empty directory
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        async def mock_get_docroot():
            return str(tmp_path)

        monkeypatch.setattr(session, "get_docroot", mock_get_docroot)

        args = CategoryListFilesArgs(name="docs")
        result_str = await category_list_files(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert result_dict["value"] == []

    @pytest.mark.asyncio
    async def test_successful_file_listing(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test successful file listing with template stripping."""
        # Setup session with category
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test")
        category = Category(dir="docs", patterns=["*.md"])
        session._cached_project = Project(name="test", categories={"docs": category}, collections={})
        set_current_session(session)

        # Create test files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "readme.md").write_text("# README")
        (docs_dir / "guide.md.mustache").write_text("# Guide {{name}}")

        async def mock_get_docroot():
            return str(tmp_path)

        monkeypatch.setattr(session, "get_docroot", mock_get_docroot)

        args = CategoryListFilesArgs(name="docs")
        result_str = await category_list_files(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        files = result_dict["value"]
        assert len(files) == 2

        # Check file structure
        for file_info in files:
            assert "path" in file_info
            assert "size" in file_info
            assert "basename" in file_info
            assert isinstance(file_info["size"], int)
            assert file_info["size"] > 0

        # Check template extension stripping
        basenames = [f["basename"] for f in files]
        assert "guide.md" in basenames  # .mustache stripped
        assert "readme.md" in basenames
