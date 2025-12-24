"""Tests for pattern matching utilities."""

from pathlib import Path

import pytest

from mcp_guide.constants import MAX_DOCUMENTS_PER_GLOB, MAX_GLOB_DEPTH
from mcp_guide.utils.pattern_matching import safe_glob_search


class TestBasicPatternMatching:
    """Tests for basic glob pattern matching."""

    @pytest.mark.asyncio
    async def test_simple_wildcard_pattern(self, temp_project_dir):
        """Test simple wildcard pattern matches correct files."""
        # Arrange
        test_dir = temp_project_dir / "test_simple"
        test_dir.mkdir()
        (test_dir / "file1.md").write_text("content1")
        (test_dir / "file2.md").write_text("content2")
        (test_dir / "file.txt").write_text("content3")

        # Act
        results = await safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file1.md", "file2.md"}

    @pytest.mark.asyncio
    async def test_no_matches_empty_list(self, temp_project_dir):
        """Test no matches returns empty list."""
        # Arrange
        test_dir = temp_project_dir / "test_no_matches"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        # Act
        results = await safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_multiple_patterns(self, temp_project_dir):
        """Test multiple patterns combine results."""
        # Arrange
        test_dir = temp_project_dir / "test_multiple"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        (test_dir / "doc.txt").write_text("content2")
        (test_dir / "readme.rst").write_text("content3")

        # Act
        results = await safe_glob_search(test_dir, ["*.md", "*.txt"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file.md", "doc.txt"}


class TestRecursivePatterns:
    """Tests for recursive glob patterns."""

    @pytest.mark.asyncio
    async def test_non_recursive_default(self, temp_project_dir):
        """Test non-recursive pattern only matches top level."""
        # Arrange
        test_dir = temp_project_dir / "test_non_recursive"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        sub_dir = test_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "nested.md").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "file.md"

    @pytest.mark.asyncio
    async def test_recursive_with_doublestar(self, temp_project_dir):
        """Test recursive pattern with ** matches nested files."""
        # Arrange
        test_dir = temp_project_dir / "test_recursive"
        test_dir.mkdir()
        (test_dir / "file.md").write_text("content1")
        sub_dir = test_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "nested.md").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 2
        result_names = {p.name for p in results}
        assert result_names == {"file.md", "nested.md"}


class TestHiddenFileExclusion:
    """Tests for hidden file and special directory exclusion."""

    @pytest.mark.asyncio
    async def test_exclude_dot_files(self, temp_project_dir):
        """Test dot files are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_dot_files"
        test_dir.mkdir()
        (test_dir / ".hidden.md").write_text("content1")
        (test_dir / "visible.md").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "visible.md"

    @pytest.mark.asyncio
    async def test_exclude_dunder_files(self, temp_project_dir):
        """Test dunder files/dirs are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_dunder"
        test_dir.mkdir()
        pycache = test_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "file.md").write_text("content1")
        (test_dir / "normal.md").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "normal.md"

    @pytest.mark.asyncio
    async def test_allow_hidden_parent_directory(self, temp_project_dir):
        """Test files under hidden parent directories are allowed."""
        # Arrange
        test_dir = temp_project_dir / "test_hidden_parent"
        test_dir.mkdir()
        hidden_dir = test_dir / ".hidden" / "sub"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "file.md").write_text("content")
        (test_dir / "visible.md").write_text("content")

        # Act
        results = await safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 2
        names = [r.name for r in results]
        assert "visible.md" in names
        assert "file.md" in names

    @pytest.mark.asyncio
    async def test_safe_glob_search_expands_tilde_in_search_dir(self, temp_project_dir, monkeypatch):
        """Ensure search_dir using ~ is expanded via LazyPath."""
        monkeypatch.setenv("HOME", str(temp_project_dir))

        docs_dir = temp_project_dir / "home-docs"
        nested_dir = docs_dir / "nested"
        nested_dir.mkdir(parents=True)

        (docs_dir / "root.md").write_text("# root doc")
        (nested_dir / "nested.md").write_text("# nested doc")

        # Non-recursive pattern
        search_dir = Path("~/home-docs")
        non_recursive_results = await safe_glob_search(search_dir, ["*.md"])
        assert sorted(p.name for p in non_recursive_results) == ["root.md"]

        # Recursive pattern
        recursive_results = await safe_glob_search(search_dir, ["**/*.md"])
        assert sorted(p.name for p in recursive_results) == ["nested.md", "root.md"]

    @pytest.mark.asyncio
    async def test_safe_glob_search_expands_env_var_in_search_dir(self, temp_project_dir, monkeypatch):
        """Ensure search_dir using ${VAR} is expanded via LazyPath."""
        monkeypatch.setenv("DOCROOT", str(temp_project_dir))

        docs_dir = temp_project_dir / "env-docs"
        nested_dir = docs_dir / "nested"
        nested_dir.mkdir(parents=True)

        (docs_dir / "env-root.md").write_text("# env root doc")
        (nested_dir / "env-nested.md").write_text("# env nested doc")

        # Non-recursive glob
        search_dir = Path("${DOCROOT}") / "env-docs"
        non_recursive_results = await safe_glob_search(search_dir, ["*.md"])
        assert sorted(p.name for p in non_recursive_results) == ["env-root.md"]

        # Recursive glob
        recursive_results = await safe_glob_search(search_dir, ["**/*.md"])
        assert sorted(p.name for p in recursive_results) == ["env-nested.md", "env-root.md"]

    @pytest.mark.asyncio
    async def test_exclude_dunder_parent_directory(self, temp_project_dir):
        """Test files under dunder parent directories are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_dunder_parent"
        test_dir.mkdir()
        dunder_dir = test_dir / "pkg" / "__pycache__" / "sub"
        dunder_dir.mkdir(parents=True)
        (dunder_dir / "file.md").write_text("content")
        (test_dir / "normal.md").write_text("content")

        # Act
        results = await safe_glob_search(test_dir, ["**/*.md"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "normal.md"


class TestExtensionlessFallback:
    """Tests for extensionless pattern fallback to .md."""

    @pytest.mark.asyncio
    async def test_extensionless_exact_match(self, temp_project_dir):
        """Test extensionless pattern prefers exact match."""
        # Arrange
        test_dir = temp_project_dir / "test_exact"
        test_dir.mkdir()
        (test_dir / "intro").write_text("content1")
        (test_dir / "intro.md").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["intro"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro"

    @pytest.mark.asyncio
    async def test_extensionless_fallback_md(self, temp_project_dir):
        """Test extensionless pattern falls back to .md."""
        # Arrange
        test_dir = temp_project_dir / "test_fallback"
        test_dir.mkdir()
        (test_dir / "intro.md").write_text("content")

        # Act
        results = await safe_glob_search(test_dir, ["intro"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro.md"

    @pytest.mark.asyncio
    async def test_pattern_with_extension_no_fallback(self, temp_project_dir):
        """Test pattern with extension doesn't use fallback."""
        # Arrange
        test_dir = temp_project_dir / "test_no_fallback"
        test_dir.mkdir()
        (test_dir / "intro.md").write_text("content1")
        (test_dir / "intro.txt").write_text("content2")

        # Act
        results = await safe_glob_search(test_dir, ["intro.txt"])

        # Assert
        assert len(results) == 1
        assert results[0].name == "intro.txt"


class TestSymlinkAndBoundaryBehavior:
    """Tests for symlink resolution, deduplication, and boundary checks."""

    @pytest.mark.asyncio
    async def test_symlink_inside_search_dir_is_deduplicated(self, temp_project_dir):
        """A symlink to a file inside search_dir should appear only once."""
        # Arrange
        search_dir = temp_project_dir / "search"
        search_dir.mkdir()

        real_file = search_dir / "target.txt"
        real_file.write_text("hello")

        symlink = search_dir / "link_to_target.txt"
        symlink.symlink_to(real_file)

        # Act
        matches = await safe_glob_search(search_dir, ["**/*.txt"])

        # Assert
        assert real_file.resolve() in [p.resolve() for p in matches]
        resolved_paths = [p.resolve() for p in matches]
        assert len(resolved_paths) == len(set(resolved_paths))

    @pytest.mark.asyncio
    async def test_symlink_pointing_outside_search_dir_is_skipped(self, temp_project_dir):
        """A symlink inside search_dir pointing outside it should be ignored."""
        # Arrange
        search_dir = temp_project_dir / "search"
        search_dir.mkdir()

        outside_dir = temp_project_dir / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "outside.txt"
        outside_file.write_text("outside")

        bad_symlink = search_dir / "link_to_outside.txt"
        bad_symlink.symlink_to(outside_file)

        # Act
        matches = await safe_glob_search(search_dir, ["**/*.txt"])

        # Assert
        assert matches == []


class TestDepthLimit:
    """Tests for MAX_GLOB_DEPTH enforcement."""

    @pytest.mark.asyncio
    async def test_respect_max_depth(self, temp_project_dir):
        """Test files beyond MAX_GLOB_DEPTH are excluded."""
        # Arrange
        test_dir = temp_project_dir / "test_depth"
        test_dir.mkdir()

        included_files = []
        excluded_files = []

        current = test_dir
        for depth in range(1, MAX_GLOB_DEPTH + 2):
            current = current / f"level_{depth}"
            current.mkdir()
            file_path = current / f"file_depth_{depth}.txt"
            file_path.write_text(f"depth {depth}")

            if depth <= MAX_GLOB_DEPTH:
                included_files.append(file_path)
            else:
                excluded_files.append(file_path)

        # Act
        results = await safe_glob_search(test_dir, ["**/*.txt"])
        result_paths = {p.resolve() for p in results}

        # Assert: all files at depth <= MAX_GLOB_DEPTH are included
        for file_path in included_files:
            assert file_path.resolve() in result_paths

        # Assert: files at depth > MAX_GLOB_DEPTH are excluded
        for file_path in excluded_files:
            assert file_path.resolve() not in result_paths


class TestDocumentLimit:
    """Tests for MAX_DOCUMENTS_PER_GLOB enforcement."""

    @pytest.mark.asyncio
    async def test_stop_at_max_documents(self, temp_project_dir):
        """Ensure a single pattern is truncated at MAX_DOCUMENTS_PER_GLOB."""
        # Arrange
        test_dir = temp_project_dir / "test_limit"
        test_dir.mkdir()

        total_files = MAX_DOCUMENTS_PER_GLOB + 50
        for i in range(total_files):
            (test_dir / f"file{i:03d}.md").write_text(f"content{i}")

        # Act
        results = await safe_glob_search(test_dir, ["*.md"])

        # Assert
        assert len(results) == MAX_DOCUMENTS_PER_GLOB

    @pytest.mark.asyncio
    async def test_combined_patterns_respects_global_limit(self, temp_project_dir):
        """Ensure MAX_DOCUMENTS_PER_GLOB is applied across all patterns."""
        # Arrange
        test_dir = temp_project_dir / "test_combined"
        test_dir.mkdir()

        for i in range(MAX_DOCUMENTS_PER_GLOB):
            (test_dir / f"doc_{i}.md").write_text("markdown")
        for i in range(MAX_DOCUMENTS_PER_GLOB):
            (test_dir / f"note_{i}.txt").write_text("text")

        # Act
        results = await safe_glob_search(test_dir, ["*.md", "*.txt"])

        # Assert
        assert len(results) <= MAX_DOCUMENTS_PER_GLOB
        assert results  # Sanity check we got some results
        suffixes = {path.suffix for path in results}
        assert suffixes & {".md", ".txt"}
