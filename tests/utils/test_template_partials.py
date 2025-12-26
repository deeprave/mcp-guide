"""Tests for template partial utilities."""

from pathlib import Path

import pytest

from mcp_guide.utils.template_partials import (
    PartialNotFoundError,
    load_partial_content,
    resolve_partial_paths,
)


class TestPartialPathResolution:
    """Test partial path resolution utilities."""

    def test_resolve_partial_paths(self):
        """Test basic partial path resolution."""
        template_path = Path("templates/_commands/status.mustache")
        includes = ["partials/_project.mustache", "partials/_header.mustache"]

        resolved = resolve_partial_paths(template_path, includes)

        # Check that paths are resolved correctly (absolute paths)
        assert len(resolved) == 2
        assert resolved[0].name == "_project.mustache"
        assert resolved[1].name == "_header.mustache"
        # Check that the parent directories are correct
        assert "partials" in str(resolved[0])
        assert "partials" in str(resolved[1])

    def test_resolve_partial_paths_nested(self):
        """Test partial path resolution with nested directories."""
        template_path = Path("templates/docs/nested/guide.mustache")
        includes = ["../_shared.mustache", "local/_footer.mustache"]

        resolved = resolve_partial_paths(template_path, includes)

        # Check that paths are resolved correctly (relative to current working directory)
        assert len(resolved) == 2
        assert resolved[0].name == "_shared.mustache"
        assert resolved[1].name == "_footer.mustache"
        # Check that the parent directories are correct
        assert "docs" in str(resolved[0])
        assert "local" in str(resolved[1])


class TestPartialSecurity:
    """Test security validation for partial paths."""

    def test_reject_absolute_paths(self):
        """Test that absolute paths are rejected."""
        template_path = Path("templates/status.mustache")
        includes = ["/etc/passwd"]

        with pytest.raises(PartialNotFoundError) as exc_info:
            resolve_partial_paths(template_path, includes)

        assert "Absolute paths not allowed" in str(exc_info.value)

    def test_reject_paths_outside_docroot(self):
        """Test that paths outside docroot are rejected."""
        template_path = Path("templates/status.mustache")
        includes = ["../../../etc/passwd"]

        with pytest.raises(PartialNotFoundError) as exc_info:
            resolve_partial_paths(template_path, includes)

        assert "outside docroot" in str(exc_info.value)

    def test_allow_relative_paths_within_docroot(self):
        """Test that relative paths within docroot are allowed."""
        template_path = Path("templates/subdir/status.mustache")
        includes = ["../partials/_project.mustache"]

        # This should work as it resolves to templates/partials/_project.mustache
        resolved = resolve_partial_paths(template_path, includes)
        assert len(resolved) == 1
        assert resolved[0].name == "_project.mustache"


class TestPartialLoading:
    """Test partial content loading."""

    def test_load_partial_content_missing_file(self):
        """Test loading non-existent partial raises error."""
        partial_path = Path("nonexistent/_partial.mustache")

        with pytest.raises(PartialNotFoundError) as exc_info:
            load_partial_content(partial_path)

        assert "nonexistent/_partial.mustache" in str(exc_info.value)
