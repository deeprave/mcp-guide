"""Tests for template partial utilities."""

from pathlib import Path

import pytest

from mcp_guide.render.partials import (
    PartialNotFoundError,
    load_partial_content,
    resolve_partial_paths,
)


class TestPartialPathResolution:
    """Test partial path resolution utilities."""

    async def test_resolve_partial_paths(self, tmp_path):
        """Test basic partial path resolution."""
        # Create temporary template structure
        templates_dir = tmp_path / "templates" / "_commands"
        partials_dir = templates_dir / "partials"  # partials relative to template dir
        templates_dir.mkdir(parents=True)
        partials_dir.mkdir(parents=True)

        # Create test files
        template_file = templates_dir / "status.mustache"
        partial1 = partials_dir / "_project.mustache"
        partial2 = partials_dir / "_header.mustache"

        template_file.write_text("{{> _project}}")
        partial1.write_text("Project content")
        partial2.write_text("Header content")

        template_path = template_file
        includes = ["partials/_project.mustache", "partials/_header.mustache"]

        resolved = await resolve_partial_paths(template_path, includes, docroot=tmp_path)

        # Check that paths are resolved correctly (absolute paths)
        assert len(resolved) == 2
        assert resolved[0].name == "_project.mustache"
        assert resolved[1].name == "_header.mustache"
        # Check that the parent directories are correct
        assert "partials" in str(resolved[0])
        assert "partials" in str(resolved[1])

    async def test_resolve_partial_paths_nested(self, tmp_path):
        """Test partial path resolution with nested directories."""
        # Create temporary nested template structure
        nested_dir = tmp_path / "templates" / "docs" / "nested"
        docs_dir = tmp_path / "templates" / "docs"
        local_dir = nested_dir / "local"
        nested_dir.mkdir(parents=True)
        local_dir.mkdir(parents=True)

        # Create test files
        template_file = nested_dir / "guide.mustache"
        shared_partial = docs_dir / "_shared.mustache"
        footer_partial = local_dir / "_footer.mustache"

        template_file.write_text("{{> _shared}}")
        shared_partial.write_text("Shared content")
        footer_partial.write_text("Footer content")

        template_path = template_file
        includes = ["../_shared.mustache", "local/_footer.mustache"]

        resolved = await resolve_partial_paths(template_path, includes, docroot=tmp_path)

        # Check that paths are resolved correctly (relative to current working directory)
        assert len(resolved) == 2
        assert resolved[0].name == "_shared.mustache"
        assert resolved[1].name == "_footer.mustache"
        # Check that the parent directories are correct
        assert "docs" in str(resolved[0])
        assert "local" in str(resolved[1])


class TestPartialSecurity:
    """Test security validation for partial paths."""

    async def test_reject_absolute_paths(self):
        """Test that absolute paths are rejected."""
        template_path = Path("templates/status.mustache")
        includes = ["/etc/passwd"]

        with pytest.raises(PartialNotFoundError) as exc_info:
            await resolve_partial_paths(template_path, includes)

        assert "Absolute paths not allowed" in str(exc_info.value)

    async def test_reject_paths_outside_docroot(self):
        """Test that paths outside docroot are rejected."""
        template_path = Path("templates/status.mustache")
        includes = ["../../../etc/passwd"]

        with pytest.raises(PartialNotFoundError) as exc_info:
            await resolve_partial_paths(template_path, includes)

        assert "outside docroot" in str(exc_info.value)

    async def test_allow_relative_paths_within_docroot(self, tmp_path):
        """Test that relative paths within docroot are allowed."""
        # Create temporary template structure
        templates_dir = tmp_path / "templates"
        subdir = templates_dir / "subdir"
        partials_dir = templates_dir / "partials"
        templates_dir.mkdir(parents=True)
        subdir.mkdir(parents=True)
        partials_dir.mkdir(parents=True)

        # Create test files
        template_file = subdir / "status.mustache"
        partial_file = partials_dir / "_project.mustache"

        template_file.write_text("{{> _project}}")
        partial_file.write_text("Project content")

        template_path = template_file
        includes = ["../partials/_project.mustache"]

        # This should work as it resolves to templates/partials/_project.mustache
        resolved = await resolve_partial_paths(template_path, includes, docroot=tmp_path)
        assert len(resolved) == 1
        assert resolved[0].name == "_project.mustache"


class TestPartialLoading:
    """Test partial content loading."""

    async def test_load_partial_content_missing_file(self):
        """Test loading non-existent partial raises error."""
        partial_path = Path("nonexistent/_partial.mustache")
        base_path = Path("templates")

        with pytest.raises(PartialNotFoundError) as exc_info:
            await load_partial_content(partial_path, base_path)

        assert "nonexistent/_partial.mustache" in str(exc_info.value)

    async def test_load_partial_content_success(self, tmp_path):
        """Test successfully loading an existing partial file."""
        # Create a temporary partial file with known content
        partial_file = tmp_path / "_partial.mustache"
        expected_content = "Hello {{name}}!"
        partial_file.write_text(expected_content, encoding="utf-8")

        # Load the content
        actual_content = await load_partial_content(partial_file, tmp_path)

        # Verify content matches exactly
        assert actual_content == expected_content
