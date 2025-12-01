"""Tests for pattern matching utilities."""

from pathlib import Path

import pytest

from mcp_guide.utils.pattern_matching import safe_glob_search


class TestBasicPatternMatching:
    """Tests for basic glob pattern matching."""

    def test_simple_wildcard_pattern(self, temp_project_dir):
        """Test simple wildcard pattern matches correct files."""
        # Arrange
        test_dir = temp_project_dir / "test_simple"
        test_dir.mkdir()
        (test_dir / "file1.md").write_text("content1")
        (test_dir / "file2.md").write_text("content2")
        (test_dir / "file.txt").write_text("content3")

        # Act
        results = safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file1.md", "file2.md"}

    def test_no_matches_empty_list(self, temp_project_dir):
        """Test no matches returns empty list."""
        # Arrange
        test_dir = temp_project_dir / "test_no_matches"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        # Act
        results = safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert results == []

    def test_multiple_patterns(self, temp_project_dir):
        """Test multiple patterns combine results."""
        # Arrange
        test_dir = temp_project_dir / "test_multiple"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        (test_dir / "doc.txt").write_text("content2")
        (test_dir / "readme.rst").write_text("content3")

        # Act
        results = safe_glob_search(test_dir, ["*.md", "*.txt"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file.md", "doc.txt"}


class TestRecursivePatterns:
    """Tests for recursive glob patterns."""

    def test_non_recursive_default(self, temp_project_dir):
        """Test non-recursive pattern only matches top level."""
        # Arrange
        test_dir = temp_project_dir / "test_non_recursive"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        sub_dir = test_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "nested.md").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "file.md"

    def test_recursive_with_doublestar(self, temp_project_dir):
        """Test recursive pattern with ** matches nested files."""
        # Arrange
        test_dir = temp_project_dir / "test_recursive"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        sub_dir = test_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "nested.md").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file.md", "nested.md"}


class TestHiddenFileExclusion:
    """Tests for hidden file and special directory exclusion."""

    def test_exclude_dot_files(self, temp_project_dir):
        """Test dot files are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_dot_files"
        test_dir.mkdir()
        (test_dir / ".hidden.md").write_text("content1")
        (test_dir / "visible.md").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "visible.md"

    def test_exclude_dunder_files(self, temp_project_dir):
        """Test dunder files/dirs are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_dunder"
        test_dir.mkdir()
        pycache = test_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "file.md").write_text("content1")
        (test_dir / "normal.md").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "normal.md"

    def test_exclude_metadata_files(self, temp_project_dir):
        """Test metadata files are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_metadata"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        (test_dir / "file.md_.json").write_text("{}")

        # Act
        results = safe_glob_search(test_dir, ["*"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "file.md"


class TestExtensionlessFallback:
    """Tests for extensionless pattern fallback to .md."""

    def test_extensionless_exact_match(self, temp_project_dir):
        """Test extensionless pattern prefers exact match."""
        # Arrange
        test_dir = temp_project_dir / "test_exact"
        test_dir.mkdir()
        (test_dir / "intro").write_text("content1")
        (test_dir / "intro.md").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["intro"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro"

    def test_extensionless_fallback_md(self, temp_project_dir):
        """Test extensionless pattern falls back to .md."""
        # Arrange
        test_dir = temp_project_dir / "test_fallback"
        test_dir.mkdir()
        (test_dir / "intro.md").write_text("content")

        # Act
        results = safe_glob_search(test_dir, ["intro"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro.md"

    def test_pattern_with_extension_no_fallback(self, temp_project_dir):
        """Test pattern with extension doesn't use fallback."""
        # Arrange
        test_dir = temp_project_dir / "test_no_fallback"
        test_dir.mkdir()
        (test_dir / "intro.md").write_text("content1")
        (test_dir / "intro.txt").write_text("content2")

        # Act
        results = safe_glob_search(test_dir, ["intro.txt"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro.txt"


class TestDepthLimit:
    """Tests for MAX_GLOB_DEPTH enforcement."""

    def test_respect_max_depth(self, temp_project_dir):
        """Test files beyond MAX_GLOB_DEPTH are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_depth"
        test_dir.mkdir()

        # Create nested structure 10 levels deep
        current = test_dir
        for i in range(10):
            current = current / f"level{i}"
            current.mkdir()
            (current / f"file{i}.md").write_text(f"content{i}")

        # Act
        results = safe_glob_search(test_dir, ["**/*.md"])

        # Assert - should only get files within depth 8
        assert len(results) <= 8
        # Verify deepest file is at most depth 8
        for result in results:
            relative = result.relative_to(test_dir.resolve())
            depth = len(relative.parts) - 1  # Subtract 1 for file itself
            assert depth <= 8


class TestDocumentLimit:
    """Tests for MAX_DOCUMENTS_PER_GLOB enforcement."""

    def test_stop_at_max_documents(self, temp_project_dir):
        """Test stops at MAX_DOCUMENTS_PER_GLOB."""
        # Arrange
        test_dir = temp_project_dir / "test_limit"
        test_dir.mkdir()

        # Create 150 files
        for i in range(150):
            (test_dir / f"file{i:03d}.md").write_text(f"content{i}")

        # Act
        results = safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 100
