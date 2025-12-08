"""Tests for immutable data models."""

import pytest

from mcp_guide.models import Category, Collection, Project, SessionState


class TestSessionState:
    """Tests for SessionState model."""

    def test_session_state_is_mutable(self):
        """SessionState should be mutable (not frozen)."""
        state = SessionState()
        state.current_dir = "/new/path"
        assert state.current_dir == "/new/path"

    def test_session_state_cache(self):
        """SessionState cache should be mutable."""
        state = SessionState()
        state.cache["key"] = "value"
        assert state.cache["key"] == "value"


class TestCategory:
    """Tests for Category model."""

    def test_category_creation(self):
        """Category can be created with valid data."""
        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        assert category.name == "docs"
        assert category.dir == "docs/"
        assert category.patterns == ["*.md"]

    def test_category_name_too_long(self):
        """Category name must be 30 chars or less."""
        with pytest.raises(ValueError, match="between 1 and 30 characters"):
            Category(name="a" * 31, dir="docs/", patterns=["*.md"])

    def test_category_name_empty(self):
        """Category name cannot be empty."""
        with pytest.raises(ValueError, match="between 1 and 30 characters"):
            Category(name="", dir="docs/", patterns=["*.md"])

    def test_category_name_invalid_characters(self):
        """Category name must only contain valid characters."""
        invalid_names = ["cat@name", "cat name", "cat/name", "cat.name"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric"):
                Category(name=name, dir="docs/", patterns=["*.md"])

    def test_category_is_frozen(self):
        """Category instances should be immutable."""
        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        with pytest.raises(AttributeError):
            category.name = "new-name"


class TestCollection:
    """Tests for Collection model."""

    def test_collection_creation(self):
        """Collection can be created with valid data."""
        collection = Collection(name="backend", categories=["api", "database"], description="Backend services")
        assert collection.name == "backend"
        assert collection.categories == ["api", "database"]
        assert collection.description == "Backend services"

    def test_collection_name_too_long(self):
        """Collection name must be 30 chars or less."""
        with pytest.raises(ValueError, match="between 1 and 30 characters"):
            Collection(name="a" * 31, categories=["docs"])

    def test_collection_name_empty(self):
        """Collection name cannot be empty."""
        with pytest.raises(ValueError, match="between 1 and 30 characters"):
            Collection(name="", categories=["docs"])

    def test_collection_name_invalid_characters(self):
        """Collection name must only contain valid characters."""
        invalid_names = ["col@name", "col name", "col/name", "col.name"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric"):
                Collection(name=name, categories=["docs"])

    def test_collection_is_frozen(self):
        """Collection instances should be immutable."""
        collection = Collection(name="backend", categories=["api"])
        with pytest.raises(AttributeError):
            collection.name = "new-name"


class TestProject:
    """Tests for Project model."""

    def test_project_name_too_long(self):
        """Project name must be 50 chars or less."""
        with pytest.raises(ValueError, match="between 1 and 50 characters"):
            Project(name="a" * 51)

    def test_project_name_empty(self):
        """Project name cannot be empty."""
        with pytest.raises(ValueError, match="between 1 and 50 characters"):
            Project(name="")

    def test_project_name_invalid_characters(self):
        """Project name must only contain valid characters."""
        invalid_names = ["proj@name", "proj name", "proj/name", "proj.name"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric"):
                Project(name=name)

    def test_project_is_frozen(self):
        """Project instances should be immutable (frozen)."""
        project = Project(
            name="test-project",
            categories=[],
            collections=[],
        )

        with pytest.raises(AttributeError):
            project.name = "new-name"

    def test_with_category_returns_new_instance(self):
        """with_category should return a new Project instance."""
        from mcp_guide.models import Category

        project = Project(
            name="test-project",
            categories=[],
            collections=[],
        )

        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        new_project = project.with_category(category)

        assert new_project is not project
        assert len(new_project.categories) == 1
        assert new_project.categories[0] == category
        assert len(project.categories) == 0  # Original unchanged

    def test_without_category_returns_new_instance(self):
        """without_category should return a new Project instance."""
        from mcp_guide.models import Category

        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        project = Project(
            name="test-project",
            categories=[category],
            collections=[],
        )

        new_project = project.without_category("docs")

        assert new_project is not project
        assert len(new_project.categories) == 0
        assert len(project.categories) == 1  # Original unchanged


class TestExtraFieldHandling:
    """Tests for models ignoring extra fields in config."""

    def test_project_ignores_extra_fields(self):
        """Project should ignore extra fields from hand-edited configs."""
        project = Project(
            name="test-project",
            categories=[],
            collections=[],
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert project.name == "test-project"
        assert project.categories == []
        assert project.collections == []
        assert not hasattr(project, "deprecated_field")
        assert not hasattr(project, "unknown_field")

    def test_category_ignores_extra_fields(self):
        """Category should ignore extra fields from hand-edited configs."""
        category = Category(
            name="docs",
            dir="docs/",
            patterns=["*.md"],
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert category.name == "docs"
        assert category.dir == "docs/"
        assert category.patterns == ["*.md"]
        assert not hasattr(category, "deprecated_field")
        assert not hasattr(category, "unknown_field")

    def test_collection_ignores_extra_fields(self):
        """Collection should ignore extra fields from hand-edited configs."""
        collection = Collection(
            name="all",
            categories=["docs", "api"],
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert collection.name == "all"
        assert collection.categories == ["docs", "api"]
        assert not hasattr(collection, "deprecated_field")
        assert not hasattr(collection, "unknown_field")
