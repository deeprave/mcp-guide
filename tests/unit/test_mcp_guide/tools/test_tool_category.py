"""Tests for category management tools."""

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from tests.helpers import create_test_session

from mcp_guide.models import Category, Collection
from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryListArgs,
    internal_category_add,
    internal_category_list,
)


async def _create_bound_session(tmp_path: Path) -> Session:
    """Create a lightweight bound session for unit tests."""
    session = Session(_config_dir_for_tests=str(tmp_path))
    config_manager = session._get_config_manager(str(tmp_path))
    _key, project = await config_manager.get_or_create_project_config("test")
    session._Session__delegate.bind(project)
    session._project_dirty = False
    set_current_session(session)
    return session


@pytest.fixture(scope="module")
async def test_session_with_categories(tmp_path_factory):
    """Module-level fixture providing a session with sample categories."""
    tmp_path = tmp_path_factory.mktemp("category_tests")
    session = await _create_bound_session(tmp_path)
    set_current_session(session)
    session._Session__delegate.bind(
        session._Session__delegate.project.with_category(
            "docs", Category(dir="documentation/", patterns=["*.md"])
        ).with_category("api", Category(dir="api/", patterns=["*.json"], description="API docs"))
    )

    yield session
    await remove_current_session()


@pytest.fixture(autouse=True)
async def setup_session(test_session_with_categories):
    """Auto-use fixture to ensure session is set for each test."""
    set_current_session(test_session_with_categories)
    yield


class TestCategoryList:
    """Tests for category_list tool."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("categories", "expected"),
        [
            (
                [],
                [],
            ),
            (
                [CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md", "*.txt"])],
                [
                    {
                        "name": "docs",
                        "dir": "documentation/",
                        "patterns": ["*.md", "*.txt"],
                        "description": None,
                    }
                ],
            ),
            (
                [
                    CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"]),
                    CategoryAddArgs(name="src", dir="src", patterns=["*.py"]),
                ],
                [
                    {"name": "docs"},
                    {"name": "src"},
                ],
            ),
        ],
        ids=["empty", "single", "multiple"],
    )
    async def test_category_list_shapes(self, tmp_path: Path, categories: list[CategoryAddArgs], expected: list[dict]):
        """category_list should return categories in the expected shape."""
        session = await _create_bound_session(tmp_path)

        for args in categories:
            await internal_category_add(args)

        result = await internal_category_list(CategoryListArgs())

        assert result.success is True
        assert len(result.value) == len(expected)
        for item, expected_item in zip(result.value, expected, strict=False):
            for key, value in expected_item.items():
                assert item[key] == value


class TestCategoryAdd:
    """Tests for category_add tool."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("args", "expected_name", "expected_dir", "expected_patterns", "expected_description"),
        [
            (
                CategoryAddArgs(name="docs", dir="docs", patterns=["README"]),
                "docs",
                "docs/",
                ["README"],
                None,
            ),
            (
                CategoryAddArgs(name="api", dir="api", patterns=["*.py"], description="API documentation"),
                "api",
                "api/",
                ["*.py"],
                "API documentation",
            ),
            (
                CategoryAddArgs(name="docs", patterns=["*.md"]),
                "docs",
                "docs/",
                ["*.md"],
                None,
            ),
            (
                CategoryAddArgs(name="code", dir="src", patterns=["*.py", "*.pyx", "*.pyi"]),
                "code",
                "src/",
                ["*.py", "*.pyx", "*.pyi"],
                None,
            ),
        ],
        ids=["minimal", "with_description", "dir_defaults_to_name", "multiple_patterns"],
    )
    async def test_category_add_success_shapes(
        self,
        tmp_path: Path,
        args: CategoryAddArgs,
        expected_name: str,
        expected_dir: str,
        expected_patterns: list[str],
        expected_description: str | None,
    ) -> None:
        """Successful category_add cases should persist the expected category shape."""
        session = await _create_bound_session(tmp_path)

        result = await internal_category_add(args)

        assert result.success is True
        project = await session.get_project()
        assert len(project.categories) == 1
        assert expected_name in project.categories
        category = project.categories[expected_name]
        assert category.dir == expected_dir
        assert category.patterns == expected_patterns
        assert category.description == expected_description

    @pytest.mark.anyio
    async def test_category_add_duplicate_name(self, tmp_path: Path) -> None:
        """Reject duplicate category name."""
        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await _create_bound_session(tmp_path)

        # First, add a category
        await internal_category_add(CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md"]))

        # Then try to add the same category again - should fail
        args = CategoryAddArgs(name="docs", dir="other", patterns=["*.txt"])
        result = await internal_category_add(args)

        assert result.success is False
        assert "already exists" in result.error.lower()
        assert len((await session.get_project()).categories) == 1
        assert (await session.get_project()).categories["docs"].dir == "documentation/"

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "invalid_name,error_contains",
        [
            ("", None),
            ("docs/api", None),
            ("a" * 31, "30 characters"),
        ],
        ids=["empty", "special_chars", "too_long"],
    )
    async def test_category_add_invalid_name(
        self, tmp_path: Path, invalid_name: str, error_contains: str | None
    ) -> None:
        """Reject invalid category names."""
        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await _create_bound_session(tmp_path)

        args = CategoryAddArgs(name=invalid_name, dir="docs", patterns=["*.md"])
        result = await internal_category_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        if error_contains:
            assert error_contains in result.error
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "field,value",
        [
            ("dir", "/absolute/path"),
            ("dir", "../parent"),
            ("description", "x" * 501),
            ("description", 'Has "quotes"'),
            ("patterns", ["/absolute/*.md"]),
            ("patterns", ["../*.md"]),
        ],
        ids=["dir_absolute", "dir_traversal", "desc_too_long", "desc_quotes", "pattern_absolute", "pattern_traversal"],
    )
    async def test_category_add_invalid_fields(self, tmp_path: Path, field: str, value: any) -> None:
        """Reject invalid directory, description, and pattern values."""
        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await _create_bound_session(tmp_path)

        kwargs = {"name": "docs", "dir": "docs", "patterns": ["*.md"]}
        kwargs[field] = value
        args = CategoryAddArgs(**kwargs)
        result = await internal_category_add(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.anyio
    async def test_category_add_empty_patterns(self, tmp_path: Path) -> None:
        """Allow empty patterns list."""
        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await _create_bound_session(tmp_path)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=[])
        result = await internal_category_add(args)

        assert result.success is True
        assert len((await session.get_project()).categories) == 1
        assert (await session.get_project()).categories["docs"].patterns == []

    @pytest.mark.anyio
    async def test_category_add_auto_saves(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Auto-save after successful add."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        update_mock = AsyncMock()
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result = await internal_category_add(args)

        assert result.success is True
        update_mock.assert_called_once()

    @pytest.mark.anyio
    async def test_category_add_save_failure(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Handle save failure gracefully."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryAddArgs

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        result = await internal_category_add(args)

        assert result.success is False
        assert "save" in result.error.lower()


class TestCategoryRemove:
    """Tests for category_remove tool."""

    @pytest.mark.anyio
    async def test_category_remove_existing(self, tmp_path: Path) -> None:
        """Remove existing category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        docs_category = Category(dir="docs", patterns=["*.md"])
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryRemoveArgs
        # Add the category first using the real API
        from mcp_guide.tools.tool_category import CategoryAddArgs

        add_args = CategoryAddArgs(name="docs", dir="docs", patterns=["*.md"])
        await internal_category_add(add_args)

        args = CategoryRemoveArgs(name="docs")
        result = await internal_category_remove(args)

        assert result.success is True
        assert "removed successfully" in result.value
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.anyio
    async def test_category_remove_nonexistent(self, tmp_path: Path) -> None:
        """Reject removing non-existent category."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        await session.get_project()
        # Project setup handled by Session
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result = await internal_category_remove(args)

        assert result.success is False
        assert result.error_type == "not_found"
        assert "does not exist" in result.error
        assert len((await session.get_project()).categories) == 0

    @pytest.mark.anyio
    async def test_category_remove_updates_single_collection(self, tmp_path: Path) -> None:
        """Remove category from single collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category and collection properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.collections["all"] = Collection(categories=["docs"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result = await internal_category_remove(args)

        assert result.success is True
        assert len((await session.get_project()).categories) == 0
        assert len((await session.get_project()).collections) == 1
        assert (await session.get_project()).collections["all"].categories == []

    @pytest.mark.anyio
    async def test_category_remove_updates_multiple_collections(self, tmp_path: Path) -> None:
        """Remove category from multiple collections."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add categories and collections properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.categories["api"] = Category(dir="api", patterns=["*.py"])
        project.categories["tests"] = Category(dir="tests", patterns=["*.py"])
        project.collections["backend"] = Collection(categories=["api", "tests"])
        project.collections["frontend"] = Collection(categories=["docs", "api"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="api")
        result = await internal_category_remove(args)

        assert result.success is True
        assert len((await session.get_project()).categories) == 2
        assert "api" not in (await session.get_project()).categories
        assert (await session.get_project()).collections["backend"].categories == ["tests"]
        assert (await session.get_project()).collections["frontend"].categories == ["docs"]

    @pytest.mark.anyio
    async def test_category_remove_not_in_collections(self, tmp_path: Path) -> None:
        """Remove category not in any collection."""
        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add categories and collection properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        project.categories["api"] = Category(dir="api", patterns=["*.py"])
        project.collections["backend"] = Collection(categories=["api"])
        set_current_session(session)

        args = CategoryRemoveArgs(name="docs")
        result = await internal_category_remove(args)

        assert result.success is True
        assert len((await session.get_project()).categories) == 1
        assert "api" in (await session.get_project()).categories
        assert (await session.get_project()).collections["backend"].categories == ["api"]

    @pytest.mark.anyio
    async def test_category_remove_auto_saves(self, tmp_path: Path, monkeypatch) -> None:
        """Verify category removal is persisted."""
        from unittest.mock import AsyncMock

        from mcp_guide.tools.tool_category import CategoryRemoveArgs, internal_category_remove

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        set_current_session(session)

        update_mock = AsyncMock(side_effect=Exception("Save failed"))
        monkeypatch.setattr(session, "update_config", update_mock)

        args = CategoryRemoveArgs(name="docs")
        result = await internal_category_remove(args)

        assert result.success is False
        assert "save" in result.error.lower()


class TestCategoryChange:
    """Tests for category_change tool."""

    @pytest.mark.anyio
    async def test_category_change_name(self, tmp_path: Path) -> None:
        """Change category name (rename)."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, internal_category_change

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Documentation")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_name="documentation")
        result = await internal_category_change(args)

        assert result.success is True
        assert "docs" not in (await session.get_project()).categories
        doc_cat = (await session.get_project()).categories["documentation"]
        assert doc_cat.dir == "docs/"
        assert doc_cat.patterns == ["*.md"]
        assert doc_cat.description == "Documentation"

    @pytest.mark.anyio
    async def test_category_change_dir(self, tmp_path: Path) -> None:
        """Change category directory."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, internal_category_change

        session = await _create_bound_session(tmp_path)
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_dir="documentation")
        result = await internal_category_change(args)

        assert result.success is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.dir == "documentation/"
        assert doc_cat.patterns == ["*.md"]

    @pytest.mark.anyio
    async def test_category_change_description(self, tmp_path: Path) -> None:
        """Change category description."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, internal_category_change

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Old")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="New description")
        result = await internal_category_change(args)

        assert result.success is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.description == "New description"
        assert doc_cat.dir == "docs/"

    @pytest.mark.anyio
    async def test_category_change_clear_description(self, tmp_path: Path) -> None:
        """Clear category description with empty string."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, internal_category_change

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"], description="Documentation")
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_description="")
        result = await internal_category_change(args)

        assert result.success is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.description is None

    @pytest.mark.anyio
    async def test_category_change_patterns(self, tmp_path: Path, monkeypatch) -> None:
        """Replace category patterns."""
        from mcp_guide.tools.tool_category import CategoryChangeArgs, internal_category_change

        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project = await session.get_project()
        # Add category properly
        project.categories["docs"] = Category(dir="docs", patterns=["*.md"])
        set_current_session(session)

        args = CategoryChangeArgs(name="docs", new_patterns=["*.rst", "*.txt"])
        result = await internal_category_change(args)

        assert result.success is True
        doc_cat = (await session.get_project()).categories["docs"]
        assert doc_cat.patterns == ["*.rst", "*.txt"]
        assert doc_cat.dir == "docs/"


class TestCategoryCollectionArgsValidation:
    """Tests for CategoryCollection*Args validation."""

    @pytest.mark.parametrize(
        "args_class,type_value,invalid_field,invalid_value,error_match",
        [
            # CategoryCollectionAddArgs
            (
                "CategoryCollectionAddArgs",
                "category",
                "categories",
                ["cat1"],
                "'categories' field is only valid for type='collection'",
            ),
            (
                "CategoryCollectionAddArgs",
                "collection",
                "dir",
                "some/path",
                "'dir' and 'patterns' fields are only valid for type='category'",
            ),
            (
                "CategoryCollectionAddArgs",
                "collection",
                "patterns",
                ["*.md"],
                "'dir' and 'patterns' fields are only valid for type='category'",
            ),
            # CategoryCollectionChangeArgs
            (
                "CategoryCollectionChangeArgs",
                "category",
                "new_categories",
                ["cat1"],
                "'new_categories' field is only valid for type='collection'",
            ),
            (
                "CategoryCollectionChangeArgs",
                "collection",
                "new_dir",
                "some/path",
                "'new_dir' and 'new_patterns' fields are only valid for type='category'",
            ),
            (
                "CategoryCollectionChangeArgs",
                "collection",
                "new_patterns",
                ["*.md"],
                "'new_dir' and 'new_patterns' fields are only valid for type='category'",
            ),
            # CategoryCollectionUpdateArgs
            (
                "CategoryCollectionUpdateArgs",
                "category",
                "add_categories",
                ["cat1"],
                "'add_categories' and 'remove_categories' fields are only valid for type='collection'",
            ),
            (
                "CategoryCollectionUpdateArgs",
                "category",
                "remove_categories",
                ["cat1"],
                "'add_categories' and 'remove_categories' fields are only valid for type='collection'",
            ),
            (
                "CategoryCollectionUpdateArgs",
                "collection",
                "add_patterns",
                ["*.md"],
                "'add_patterns' and 'remove_patterns' fields are only valid for type='category'",
            ),
            (
                "CategoryCollectionUpdateArgs",
                "collection",
                "remove_patterns",
                ["*.md"],
                "'add_patterns' and 'remove_patterns' fields are only valid for type='category'",
            ),
        ],
        ids=[
            "add_category_with_categories",
            "add_collection_with_dir",
            "add_collection_with_patterns",
            "change_category_with_new_categories",
            "change_collection_with_new_dir",
            "change_collection_with_new_patterns",
            "update_category_with_add_categories",
            "update_category_with_remove_categories",
            "update_collection_with_add_patterns",
            "update_collection_with_remove_patterns",
        ],
    )
    @pytest.mark.anyio
    async def test_incompatible_field_validation(
        self, args_class: str, type_value: str, invalid_field: str, invalid_value, error_match: str
    ) -> None:
        """Reject incompatible fields based on type."""
        from pydantic import ValidationError

        from mcp_guide.tools import tool_category

        cls = getattr(tool_category, args_class)
        kwargs = {"type": type_value, "name": "test", invalid_field: invalid_value}

        with pytest.raises(ValidationError, match=error_match):
            cls(**kwargs)

    @pytest.mark.parametrize(
        "args_class,type_value,valid_fields",
        [
            ("CategoryCollectionAddArgs", "category", {"dir": "docs", "patterns": ["*.md"]}),
            ("CategoryCollectionAddArgs", "collection", {"categories": ["cat1", "cat2"]}),
            ("CategoryCollectionChangeArgs", "category", {"new_dir": "docs", "new_patterns": ["*.md"]}),
            ("CategoryCollectionChangeArgs", "collection", {"new_categories": ["cat1", "cat2"]}),
            ("CategoryCollectionUpdateArgs", "category", {"add_patterns": ["*.md"], "remove_patterns": ["*.txt"]}),
            ("CategoryCollectionUpdateArgs", "collection", {"add_categories": ["cat1"], "remove_categories": ["cat2"]}),
        ],
        ids=[
            "add_valid_category",
            "add_valid_collection",
            "change_valid_category",
            "change_valid_collection",
            "update_valid_category",
            "update_valid_collection",
        ],
    )
    @pytest.mark.anyio
    async def test_valid_field_combinations(self, args_class: str, type_value: str, valid_fields: dict) -> None:
        """Accept valid field combinations."""
        from mcp_guide.tools import tool_category

        cls = getattr(tool_category, args_class)
        kwargs = {"type": type_value, "name": "test", **valid_fields}
        args = cls(**kwargs)

        assert args.type == type_value
        for field, value in valid_fields.items():
            assert getattr(args, field) == value
