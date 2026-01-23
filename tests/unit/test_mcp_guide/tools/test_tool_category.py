"""Tests for category management tools."""

import json
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.models import Category, Collection
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryListArgs,
    category_list,
    internal_category_add,
)


@pytest.fixture(scope="module")
async def test_session_with_categories(tmp_path_factory):
    """Module-level fixture providing a session with sample categories."""
    tmp_path = tmp_path_factory.mktemp("category_tests")
    session = Session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)

    # Add sample categories using the real API
    docs_args = CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md"])
    await internal_category_add(docs_args)

    api_args = CategoryAddArgs(name="api", dir="api", patterns=["*.json"], description="API docs")
    await internal_category_add(api_args)

    yield session
    await remove_current_session("test")


@pytest.fixture(autouse=True)
async def setup_session(test_session_with_categories):
    """Auto-use fixture to ensure session is set for each test."""
    set_current_session(test_session_with_categories)
    yield


class TestCategoryList:
    """Tests for category_list tool."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, project_dir: Path) -> Generator[None, None, None]:
        """Setup and teardown for each test."""
        yield

    @pytest.mark.asyncio
    async def test_list_empty_categories(self, tmp_path: Path) -> None:
        """List empty categories returns empty list."""
        session = Session("test", _config_dir_for_tests=str(tmp_path))
        # Create empty project
        await session.get_project()

        set_current_session(session)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert result_dict["value"] == []

    @pytest.mark.asyncio
    async def test_list_single_category(self, tmp_path: Path) -> None:
        """List single category returns all fields."""
        categories_dict = {
            "docs": Category(
                dir="documentation",
                patterns=["*.md", "*.txt"],
            )
        }
        session = Session("test", _config_dir_for_tests=str(tmp_path))

        # Add a category to the project
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        set_current_session(session)

        add_args = CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md", "*.txt"])
        await category_add(add_args)

        args = CategoryListArgs()
        result_str = await category_list(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len(result_dict["value"]) == 1
        assert result_dict["value"][0]["name"] == "docs"
        assert result_dict["value"][0]["dir"] == "documentation/"
        assert result_dict["value"][0]["patterns"] == ["*.md", "*.txt"]
        assert result_dict["value"][0]["description"] is None

    @pytest.mark.asyncio
    async def test_list_multiple_categories(self, tmp_path: Path) -> None:
        """List multiple categories returns all."""
        session = Session("test", _config_dir_for_tests=str(tmp_path))

        # Add multiple categories to the project
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        set_current_session(session)

        await category_add(CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]))
        await category_add(CategoryAddArgs(name="src", dir="src", patterns=["*.py"]))

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
        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
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

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["README"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "docs" in result_dict["value"]
        assert len((await session.get_project()).categories) == 1
        assert "docs" in (await session.get_project()).categories
        assert (await session.get_project()).categories["docs"].dir == "docs/"
        assert (await session.get_project()).categories["docs"].patterns == ["README"]
        assert (await session.get_project()).categories["docs"].description is None

    @pytest.mark.asyncio
    async def test_category_add_with_description(self, tmp_path: Path) -> None:
        """Add category with all args."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="api", dir="api", patterns=["*.py"], description="API documentation")
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 1
        assert "api" in (await session.get_project()).categories
        assert (await session.get_project()).categories["api"].description == "API documentation"

    @pytest.mark.asyncio
    async def test_category_add_dir_defaults_to_name(self, tmp_path: Path) -> None:
        """When dir is omitted, it defaults to name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        # Omit dir parameter
        args = CategoryAddArgs(name="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 1
        # Verify dir defaulted to name
        assert (await session.get_project()).categories["docs"].dir == "docs/"
        assert "docs" in (await session.get_project()).categories

    @pytest.mark.asyncio
    async def test_category_add_multiple_patterns(self, tmp_path: Path) -> None:
        """Add category with multiple patterns."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="code", dir="src", patterns=["*.py", "*.pyx", "*.pyi"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert (await session.get_project()).categories["code"].patterns == ["*.py", "*.pyx", "*.pyi"]

    @pytest.mark.asyncio
    async def test_category_add_duplicate_name(self, tmp_path: Path) -> None:
        """Reject duplicate category name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        set_current_session(session)

        # First, add a category
        await category_add(CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md"]))

        # Then try to add the same category again - should fail
        args = CategoryAddArgs(name="docs", dir="other", patterns=["*.txt"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert "already exists" in result_dict["error"].lower()
        assert len((await session.get_project()).categories) == 1
        assert (await session.get_project()).categories["docs"].dir == "documentation/"

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_empty(self, tmp_path: Path) -> None:
        """Reject invalid name (empty)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_special_chars(self, tmp_path: Path) -> None:
        """Reject invalid name (special chars)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs/api", dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_name_too_long(self, tmp_path: Path) -> None:
        """Reject invalid name (exceeds 30 characters)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="a" * 31, dir="docs", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert "30 characters" in result_dict["error"]
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_directory_absolute(self, tmp_path: Path) -> None:
        """Reject invalid directory (absolute path)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="/absolute/path", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_directory_traversal(self, tmp_path: Path) -> None:
        """Reject invalid directory (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="../parent", patterns=["*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_too_long(self, tmp_path: Path) -> None:
        """Reject invalid description (too long)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description="x" * 501)
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_description_quotes(self, tmp_path: Path) -> None:
        """Reject invalid description (quotes)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"], description='Has "quotes"')
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_absolute(self, tmp_path: Path) -> None:
        """Reject invalid pattern (absolute path)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["/absolute/*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_invalid_pattern_traversal(self, tmp_path: Path) -> None:
        """Reject invalid pattern (traversal)."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["../*.md"])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_add_empty_patterns(self, tmp_path: Path) -> None:
        """Allow empty patterns list."""
        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=[])
        result_str = await category_add(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 1
        assert (await session.get_project()).categories["docs"].patterns == []

    @pytest.mark.asyncio
    async def test_category_add_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Auto-save after successful add."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs, category_add

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
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

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
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

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        docs_category = Category(dir="docs", patterns=["*.md"])
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryRemoveArgs
        # Add the category first using the real API
        from mcp_guide.tools.tool_category import CategoryAddArgs, internal_category_add

        add_args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        await internal_category_add(add_args)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "removed successfully" in result_dict["value"]
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_nonexistent(self, tmp_path: Path) -> None:
        """Reject removing non-existent category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is False
        assert result_dict["error_type"] == "not_found"
        assert "does not exist" in result_dict["error"]
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.asyncio
    async def test_category_remove_updates_single_collection(self, tmp_path: Path) -> None:
        """Remove category from single collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category and collection properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.collections["all"] = Collection(categories=["docs"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 0
        assert len((await session.get_project()).collections) == 1
        assert (await session.get_project()).collections["all"].categories == []

    @pytest.mark.asyncio
    async def test_category_remove_updates_multiple_collections(self, tmp_path: Path) -> None:
        """Remove category from multiple collections."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add categories and collections properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.categories["api"] = Category(dir="api", patterns=["*.py"])
        project.categories["tests"] = Category(dir="tests", patterns=["*.py"])
        project.collections["backend"] = Collection(categories=["api", "tests"])
        project.collections["frontend"] = Collection(categories=["docs", "api"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="api")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 2
        assert "api" not in (await session.get_project()).categories
        assert (await session.get_project()).collections["backend"].categories == ["tests"]
        assert (await session.get_project()).collections["frontend"].categories == ["docs"]

    @pytest.mark.asyncio
    async def test_category_remove_not_in_collections(self, tmp_path: Path) -> None:
        """Remove category not in any collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add categories and collection properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.categories["api"] = Category(dir="api", patterns=["*.py"])
        project.collections["backend"] = Collection(categories=["api"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result_str = await category_remove(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert len((await session.get_project()).categories) == 1
        assert "api" in (await session.get_project()).categories
        assert (await session.get_project()).collections["backend"].categories == ["api"]

    @pytest.mark.asyncio
    async def test_category_remove_auto_saves(self, tmp_path: Path, monkeypatch) -> None:
        """Verify category removal is persisted."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryRemoveArgs, category_remove

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
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

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Documentation")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        assert "docs" not in (await session.get_project()).categories
        doc_cat = (await session.get_project()).categories["documentation"]
        assert doc_cat.dir == "docs/"
        assert doc_cat.patterns == ["*.md"]
        assert doc_cat.description == "Documentation"

    @pytest.mark.asyncio
    async def test_category_change_dir(self, tmp_path: Path) -> None:
        """Change category directory."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_dir="documentation")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.dir == "documentation/"
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.asyncio
    async def test_category_change_description(self, tmp_path: Path) -> None:
        """Change category description."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Old")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="New description")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.description == "New description"
        assert doc_cat.dir == "docs/"

    @pytest.mark.asyncio
    async def test_category_change_clear_description(self, tmp_path: Path) -> None:
        """Clear category description with empty string."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Documentation")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="")
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.description is None

    @pytest.mark.asyncio
    async def test_category_change_patterns(self, tmp_path: Path, monkeypatch) -> None:
        """Replace category patterns."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, category_change

        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_patterns=["*.rst", "*.txt"])
        result_str = await category_change(args)
        result_dict = json.loads(result_str)

        assert result_dict["success"] is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.patterns == ["*.rst", "*.txt"]
        assert doc_cat.dir == "docs/"
