"""Tests for startup-instruction flag validation."""

import pytest

from mcp_guide.models.project import Category, Collection, Project
from mcp_guide.workflow.flags import parse_startup_expression, validate_startup_expression


class TestParseStartupExpression:
    """Test expression parsing."""

    def test_single_category(self):
        """Parse single category."""
        categories, collections = parse_startup_expression("docs")
        assert categories == ["docs"]
        assert collections == []

    def test_single_collection(self):
        """Parse single collection."""
        categories, collections = parse_startup_expression("@guidelines")
        assert categories == []
        assert collections == ["guidelines"]

    def test_multiple_categories(self):
        """Parse multiple categories."""
        categories, collections = parse_startup_expression("docs,examples")
        assert categories == ["docs", "examples"]
        assert collections == []

    def test_mixed_categories_and_collections(self):
        """Parse mixed categories and collections."""
        categories, collections = parse_startup_expression("docs,@guidelines,examples")
        assert categories == ["docs", "examples"]
        assert collections == ["guidelines"]

    def test_with_patterns(self):
        """Parse expression with patterns (patterns ignored)."""
        categories, collections = parse_startup_expression("docs/README*,@guidelines")
        assert categories == ["docs"]
        assert collections == ["guidelines"]

    def test_whitespace_handling(self):
        """Parse expression with whitespace."""
        categories, collections = parse_startup_expression(" docs , @guidelines , examples ")
        assert categories == ["docs", "examples"]
        assert collections == ["guidelines"]


class TestValidateStartupExpression:
    """Test expression validation."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create test project."""
        return Project(
            name="test",
            docroot=tmp_path,
            categories={
                "docs": Category(name="docs", dir="docs", patterns=["*.md"]),
                "examples": Category(name="examples", dir="examples", patterns=["*.py"]),
            },
            collections={
                "guidelines": Collection(name="guidelines", categories=["docs"]),
            },
        )

    def test_valid_category(self, project):
        """Validate existing category."""
        result = validate_startup_expression("docs", project)
        assert result.success

    def test_valid_collection(self, project):
        """Validate existing collection."""
        result = validate_startup_expression("@guidelines", project)
        assert result.success

    def test_valid_mixed(self, project):
        """Validate mixed categories and collections."""
        result = validate_startup_expression("docs,@guidelines,examples", project)
        assert result.success

    def test_invalid_category(self, project):
        """Reject non-existent category."""
        result = validate_startup_expression("nonexistent", project)
        assert not result.success
        assert "category 'nonexistent' not found" in result.error.lower()

    def test_invalid_collection(self, project):
        """Reject non-existent collection."""
        result = validate_startup_expression("@nonexistent", project)
        assert not result.success
        assert "collection 'nonexistent' not found" in result.error.lower()

    def test_pattern_ignored(self, project):
        """Patterns not validated."""
        result = validate_startup_expression("docs/README*", project)
        assert result.success

    def test_empty_expression(self, project):
        """Empty expression is valid."""
        result = validate_startup_expression("", project)
        assert result.success
