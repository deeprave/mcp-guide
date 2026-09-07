"""Tests for export tracking models."""

import pytest

from mcp_guide.models.project import ExportedTo, Project


@pytest.mark.parametrize("pattern", [None, "*.md"], ids=["whole-expression", "pattern"])
def test_export_entries_insert_replace_and_preserve_other_entries(pattern):
    original = Project(name="test").upsert_export_entry("guide", None, "/guide.md", "other")
    assert original.get_export_entry("docs", pattern) is None

    inserted = original.upsert_export_entry("docs", pattern, "/old.md", "initial", exported_at=10)
    assert inserted.get_export_entry("docs", pattern) == ExportedTo("/old.md", "initial", 10)
    assert original.get_export_entry("docs", pattern) is None

    updated = inserted.upsert_export_entry("docs", pattern, "/new.md", "changed", exported_at=20)
    assert updated.get_export_entry("docs", pattern) == ExportedTo("/new.md", "changed", 20)
    assert updated.get_export_entry("guide", None) == original.get_export_entry("guide", None)
    assert len(updated.exports) == 2
    assert inserted.get_export_entry("docs", pattern).path == "/old.md"


class TestMetadataHashComputation:
    """Tests for metadata hash computation."""

    @pytest.mark.parametrize(
        "files_setup,expected",
        [
            ("empty", None),
            ("single", lambda h: len(h) == 8),
        ],
    )
    def test_hash_computation(self, files_setup, expected):
        """Test hash computation for various file list scenarios."""
        from datetime import datetime

        from mcp_guide.discovery.files import FileInfo
        from mcp_guide.tools.tool_content import compute_metadata_hash

        if files_setup == "empty":
            files = []
        elif files_setup == "single":
            from pathlib import Path

            file_path = Path("/virtual/docs/a.md")
            files = [
                FileInfo(
                    path=file_path,
                    size=100,
                    content_size=100,
                    mtime=datetime.fromtimestamp(1000),
                    name="a.md",
                ),
            ]

        hash_val = compute_metadata_hash(files)
        assert expected(hash_val) if callable(expected) else hash_val == expected

    def test_same_filename_different_paths(self):
        """Test that files with same name in different directories produce different hashes."""
        from datetime import datetime
        from pathlib import Path

        from mcp_guide.discovery.files import FileInfo
        from mcp_guide.tools.tool_content import compute_metadata_hash

        file1_path = Path("/virtual/docs/dir1/file.md")
        file2_path = Path("/virtual/docs/dir2/file.md")

        files1 = [
            FileInfo(
                path=file1_path,
                size=100,
                content_size=100,
                mtime=datetime.fromtimestamp(1000),
                name="file.md",
            ),
        ]

        files2 = [
            FileInfo(
                path=file2_path,
                size=100,
                content_size=100,
                mtime=datetime.fromtimestamp(1000),
                name="file.md",
            ),
        ]

        hash1 = compute_metadata_hash(files1)
        hash2 = compute_metadata_hash(files2)
        assert hash1 != hash2, "Files with same name in different directories must have different hashes"
