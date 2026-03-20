"""Tests for mcp_guide validation functions."""

import pytest

from mcp_guide.core.validation import ArgValidationError
from mcp_guide.models import Category, Project
from mcp_guide.validation import validate_categories_exist


@pytest.fixture
def test_project():
    """Create a test project with sample categories."""
    return Project(
        name="test-project",
        categories={
            "docs": Category(dir="docs", patterns=["*.md"]),
            "api": Category(dir="api", patterns=["*.py"]),
            "tests": Category(dir="tests", patterns=["test_*.py"]),
        },
    )


class TestValidateCategoriesExist:
    """Tests for validate_categories_exist function."""

    def test_all_categories_exist_no_error(self, test_project):
        """All categories exist, no error should be raised."""
        validate_categories_exist(test_project, ["docs", "api"])
        validate_categories_exist(test_project, ["docs", "api", "tests"])

    def test_some_categories_missing_raises_error(self, test_project):
        """Some categories missing, should raise ArgValidationError with all missing."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_categories_exist(test_project, ["docs", "missing1", "api", "missing2"])

        errors = exc_info.value.errors
        assert len(errors) == 2
        assert all(err["field"] == "categories" for err in errors)

        error_messages = [err["message"] for err in errors]
        for missing in ("missing1", "missing2"):
            assert any(missing in msg for msg in error_messages)

    def test_all_categories_missing_raises_error(self, test_project):
        """All categories missing, should raise ArgValidationError."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_categories_exist(test_project, ["missing1", "missing2"])

        errors = exc_info.value.errors
        assert len(errors) == 2
        assert all(err["field"] == "categories" for err in errors)

        error_messages = [err["message"] for err in errors]
        for missing in ("missing1", "missing2"):
            assert any(missing in msg for msg in error_messages)

    def test_empty_list_no_error(self, test_project):
        """Empty list should not raise error."""
        validate_categories_exist(test_project, [])

    def test_empty_project_empty_list_no_error(self):
        """Empty project with empty category list should not raise error."""
        empty_project = Project(name="empty-project", categories={})
        validate_categories_exist(empty_project, [])

    def test_empty_project_nonempty_list_raises_error(self):
        """Empty project with non-empty category list should raise error."""
        empty_project = Project(name="empty-project", categories={})

        with pytest.raises(ArgValidationError) as exc_info:
            validate_categories_exist(empty_project, ["docs", "api"])

        errors = exc_info.value.errors
        assert len(errors) == 2
        assert all(err["field"] == "categories" for err in errors)

        error_messages = [err["message"] for err in errors]
        for missing in ("docs", "api"):
            assert any(missing in msg for msg in error_messages)
