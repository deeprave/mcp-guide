"""Tests for immutable data models."""

import pytest
from pydantic import ValidationError

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


class TestCollection:
    """Tests for Collection model."""

    def test_collection_creation(self):
        """Collection can be created with valid data."""
        collection = Collection(categories=["api", "database"], description="Backend services")
        assert collection.categories == ["api", "database"]
        assert collection.description == "Backend services"


class TestProject:
    """Tests for Project model."""

    @pytest.mark.parametrize(
        "scenario,name,expected_error",
        [
            ("too_long", "a" * 51, "between 1 and 50 characters"),
            ("empty", "", "between 1 and 50 characters"),
            ("invalid_at", "proj@name", "must contain only alphanumeric"),
            ("invalid_space", "proj name", "must contain only alphanumeric"),
            ("invalid_slash", "proj/name", "must contain only alphanumeric"),
            ("invalid_dot", "proj.name", "must contain only alphanumeric"),
        ],
        ids=["too_long", "empty", "invalid_at", "invalid_space", "invalid_slash", "invalid_dot"],
    )
    def test_project_name_validation(self, scenario, name, expected_error):
        """Project name must meet validation requirements."""
        with pytest.raises(ValueError, match=expected_error):
            Project(name=name)

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

    @pytest.mark.parametrize(
        "paths,error_type,error_match",
        [
            (["relative/path"], ValueError, None),
            (["/etc"], ValidationError, "System directory not allowed"),
            ([""], ValueError, None),
        ],
        ids=["relative_path", "system_directory", "empty_string"],
    )
    def test_additional_read_paths_validation(self, paths, error_type, error_match):
        """Additional read paths should reject invalid paths."""
        if error_match:
            with pytest.raises(error_type, match=error_match):
                Project(name="test", additional_read_paths=paths)
        else:
            with pytest.raises(error_type):
                Project(name="test", additional_read_paths=paths)

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
