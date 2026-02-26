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
        category = Category(dir="docs/", patterns=["*.md"])
        assert category.dir == "docs/"
        assert category.patterns == ["*.md"]

    def test_category_has_name_field(self):
        """Category should have name field (set by with_category)."""
        category = Category(dir="docs", patterns=["README"])
        assert hasattr(category, "name")
        assert category.name == ""  # Empty by default, set by with_category
        # Should only have dir, patterns, description
        assert hasattr(category, "dir")
        assert hasattr(category, "patterns")
        assert hasattr(category, "description")

    def test_category_is_frozen(self):
        """Category instances should be immutable."""
        category = Category(dir="docs/", patterns=["*.md"])
        with pytest.raises(AttributeError):
            category.dir = "new-dir"


class TestCollection:
    """Tests for Collection model."""

    def test_collection_creation(self):
        """Collection can be created with valid data."""
        collection = Collection(categories=["api", "database"], description="Backend services")
        assert collection.categories == ["api", "database"]
        assert collection.description == "Backend services"

    def test_collection_without_name_field(self):
        """Collection should not have name field (name becomes dict key)."""
        collection = Collection(categories=["docs"], description="All docs")
        assert not hasattr(collection, "name")
        # Should only have categories, description
        assert hasattr(collection, "categories")
        assert hasattr(collection, "description")

    def test_collection_is_frozen(self):
        """Collection instances should be immutable."""
        collection = Collection(categories=["api"])
        with pytest.raises(AttributeError):
            collection.categories = ["new-categories"]


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
            categories={},
            collections={},
        )

        with pytest.raises(AttributeError):
            project.name = "new-name"

    def test_with_category_returns_new_instance(self):
        """with_category should return a new Project instance."""
        from mcp_guide.models import Category

        project = Project(
            name="test-project",
            categories={},
            collections={},
        )

        category = Category(dir="docs/", patterns=["README"])
        new_project = project.with_category("docs", category)

        assert new_project is not project
        assert len(new_project.categories) == 1
        assert "docs" in new_project.categories
        assert new_project.categories["docs"].name == "docs"  # Name is set by with_category
        assert new_project.categories["docs"].dir == category.dir
        assert new_project.categories["docs"].patterns == category.patterns
        assert len(project.categories) == 0  # Original unchanged

    def test_without_category_returns_new_instance(self):
        """without_category should return a new Project instance."""
        from mcp_guide.models import Category

        category = Category(dir="docs/", patterns=["*.md"])
        project = Project(
            name="test-project",
            categories={"docs": category},
            collections={},
        )

        new_project = project.without_category("docs")

        assert new_project is not project
        assert len(new_project.categories) == 0
        assert len(project.categories) == 1  # Original unchanged

    def test_categories_as_dict(self):
        """Categories should be stored as dict[str, Category]."""
        from mcp_guide.models import Category

        category = Category(dir="docs", patterns=["*.md"])
        project = Project(name="test", categories={"docs": category})

        assert isinstance(project.categories, dict)
        assert "docs" in project.categories
        assert project.categories["docs"] == category

    def test_collections_as_dict(self):
        """Collections should be stored as dict[str, Collection]."""
        from mcp_guide.models import Collection

        collection = Collection(categories=["docs"], description="All docs")
        project = Project(name="test", collections={"all": collection})

        assert isinstance(project.collections, dict)
        assert "all" in project.collections
        assert project.collections["all"] == collection

    def test_with_category_dict_based(self):
        """with_category should work with dict-based categories."""
        from mcp_guide.models import Category

        project = Project(name="test")
        category = Category(dir="docs", patterns=["README"])
        new_project = project.with_category("docs", category)

        assert new_project is not project
        assert len(new_project.categories) == 1
        assert "docs" in new_project.categories
        assert new_project.categories["docs"].name == "docs"
        assert new_project.categories["docs"].dir == category.dir
        assert new_project.categories["docs"].patterns == category.patterns

    def test_without_category_dict_based(self):
        """without_category should work with dict-based categories."""
        from mcp_guide.models import Category

        category = Category(dir="docs", patterns=["*.md"])
        project = Project(name="test", categories={"docs": category})
        new_project = project.without_category("docs")

        assert new_project is not project
        assert len(new_project.categories) == 0
        assert "docs" not in new_project.categories


class TestAllowedPaths:
    """Tests for Project.allowed_paths field."""

    def test_project_has_default_allowed_paths(self):
        """Project should have default allowed_write_paths when created."""
        from mcp_guide.models import DEFAULT_ALLOWED_WRITE_PATHS

        project = Project(name="test")
        assert project.allowed_write_paths == DEFAULT_ALLOWED_WRITE_PATHS
        assert project.allowed_write_paths is not DEFAULT_ALLOWED_WRITE_PATHS  # Should be a copy

    def test_additional_read_paths_accepts_valid_absolute_path(self, tmp_path):
        """Valid absolute, non-system additional_read_paths should be accepted."""
        valid_path = tmp_path / "data" / "files"
        valid_path.mkdir(parents=True, exist_ok=True)

        project = Project(name="test", additional_read_paths=[str(valid_path)])
        # Should not raise and should preserve the provided path
        assert str(valid_path) in project.additional_read_paths

    def test_additional_read_paths_rejects_relative_path(self):
        """Relative paths should raise ValueError for additional_read_paths."""
        with pytest.raises(ValueError):
            Project(name="test", additional_read_paths=["relative/path"])

    def test_additional_read_paths_rejects_system_directory_with_message(self):
        """System directories (e.g. /etc) should raise ValidationError with expected message."""
        from pydantic import ValidationError

        system_path = "/etc"

        with pytest.raises(ValidationError, match="System directory not allowed"):
            Project(name="test", additional_read_paths=[system_path])

    def test_additional_read_paths_rejects_empty_string(self):
        """Empty-string additional_read_paths entries should raise ValueError."""
        with pytest.raises(ValueError):
            Project(name="test", additional_read_paths=[""])

    def test_project_with_custom_allowed_paths(self):
        """Project can be created with custom allowed_write_paths."""
        custom_paths = ["custom/", "other/"]
        project = Project(name="test", allowed_write_paths=custom_paths)
        assert project.allowed_write_paths == custom_paths

    def test_allowed_paths_requires_trailing_slash(self):
        """Allowed write paths must have trailing slashes."""
        with pytest.raises(ValueError, match="trailing slash"):
            Project(name="test", allowed_write_paths=["docs"])

    def test_allowed_paths_preserved_on_modification(self):
        """with_category and without_category should preserve allowed_write_paths."""
        custom_paths = ["custom/"]
        project = Project(name="test", allowed_write_paths=custom_paths)

        category = Category(dir="docs/", patterns=["*.md"])
        new_project = project.with_category("docs", category)

        assert new_project.allowed_write_paths == custom_paths


class TestExtraFieldHandling:
    """Tests for models ignoring extra fields in config."""

    def test_project_ignores_extra_fields(self):
        """Project should ignore extra fields from hand-edited configs."""
        project = Project(
            name="test-project",
            categories={},
            collections={},
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert project.name == "test-project"
        assert project.categories == {}
        assert project.collections == {}
        assert not hasattr(project, "deprecated_field")
        assert not hasattr(project, "unknown_field")

    def test_category_ignores_extra_fields(self):
        """Category should ignore extra fields from hand-edited configs."""
        category = Category(
            dir="docs/",
            patterns=["*.md"],
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert category.dir == "docs/"
        assert category.patterns == ["*.md"]
        assert not hasattr(category, "deprecated_field")
        assert not hasattr(category, "unknown_field")

    def test_collection_ignores_extra_fields(self):
        """Collection should ignore extra fields from hand-edited configs."""
        collection = Collection(
            categories=["docs", "api"],
            deprecated_field="old_value",  # type: ignore
            unknown_field=123,  # type: ignore
        )
        assert collection.categories == ["docs", "api"]
        assert not hasattr(collection, "deprecated_field")
        assert not hasattr(collection, "unknown_field")
