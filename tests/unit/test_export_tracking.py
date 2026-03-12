"""Tests for export tracking models."""

import pytest

from mcp_guide.models.project import Category, ExportedTo, Project


class TestExportedTo:
    """Tests for ExportedTo dataclass."""

    def test_create_exported_to(self):
        """Test creating ExportedTo instance."""
        exported = ExportedTo(path="/path/to/export.md", metadata_hash="a3f5c8d1")
        assert exported.path == "/path/to/export.md"
        assert exported.metadata_hash == "a3f5c8d1"

    def test_exported_to_immutable(self):
        """Test ExportedTo is immutable."""
        exported = ExportedTo(path="/path/to/export.md", metadata_hash="a3f5c8d1")
        with pytest.raises(AttributeError):
            exported.path = "/new/path"  # type: ignore


class TestProjectExports:
    """Tests for Project.exports field."""

    def test_project_has_exports_field(self):
        """Test Project has exports field."""
        project = Project(name="test")
        assert hasattr(project, "exports")
        assert isinstance(project.exports, dict)
        assert len(project.exports) == 0

    def test_project_exports_with_entries(self):
        """Test Project with export entries."""
        exported = ExportedTo(path="/export.md", metadata_hash="a3f5c8d1")
        project = Project(
            name="test",
            exports={("docs", None): exported},
        )
        assert len(project.exports) == 1
        assert ("docs", None) in project.exports
        assert project.exports[("docs", None)].path == "/export.md"
        assert project.exports[("docs", None)].metadata_hash == "a3f5c8d1"

    def test_project_exports_multiple_entries(self):
        """Test Project with multiple export entries."""
        exported1 = ExportedTo(path="/export1.md", metadata_hash="a3f5c8d1")
        exported2 = ExportedTo(path="/export2.md", metadata_hash="b2e4f9a7")
        project = Project(
            name="test",
            exports={
                ("docs", None): exported1,
                ("docs", "*.md"): exported2,
            },
        )
        assert len(project.exports) == 2
        assert project.exports[("docs", None)].metadata_hash == "a3f5c8d1"
        assert project.exports[("docs", "*.md")].metadata_hash == "b2e4f9a7"


class TestProjectExportMethods:
    """Tests for Project export tracking methods."""

    def test_get_export_entry_not_found(self):
        """Test get_export_entry returns None when not found."""
        project = Project(name="test")
        result = project.get_export_entry("docs", None)
        assert result is None

    def test_get_export_entry_found(self):
        """Test get_export_entry returns entry when found."""
        exported = ExportedTo(path="/export.md", metadata_hash="a3f5c8d1")
        project = Project(name="test", exports={("docs", None): exported})
        result = project.get_export_entry("docs", None)
        assert result is not None
        assert result.path == "/export.md"
        assert result.metadata_hash == "a3f5c8d1"

    def test_get_export_entry_with_pattern(self):
        """Test get_export_entry with pattern."""
        exported = ExportedTo(path="/export.md", metadata_hash="a3f5c8d1")
        project = Project(name="test", exports={("docs", "*.md"): exported})
        result = project.get_export_entry("docs", "*.md")
        assert result is not None
        assert result.path == "/export.md"

    def test_upsert_export_entry_new(self):
        """Test upsert_export_entry adds new entry."""
        project = Project(name="test")
        new_project = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
        assert len(new_project.exports) == 1
        assert ("docs", None) in new_project.exports
        assert new_project.exports[("docs", None)].path == "/export.md"
        assert new_project.exports[("docs", None)].metadata_hash == "a3f5c8d1"

    def test_upsert_export_entry_update(self):
        """Test upsert_export_entry updates existing entry."""
        exported = ExportedTo(path="/old.md", metadata_hash="a3f5c8d1")
        project = Project(name="test", exports={("docs", None): exported})
        new_project = project.upsert_export_entry("docs", None, "/new.md", "c1d2e3f4")
        assert len(new_project.exports) == 1
        assert new_project.exports[("docs", None)].path == "/new.md"
        assert new_project.exports[("docs", None)].metadata_hash == "c1d2e3f4"

    def test_upsert_export_entry_preserves_other_entries(self):
        """Test upsert_export_entry preserves other entries."""
        exported1 = ExportedTo(path="/export1.md", metadata_hash="a3f5c8d1")
        exported2 = ExportedTo(path="/export2.md", metadata_hash="b2e4f9a7")
        project = Project(
            name="test",
            exports={
                ("docs", None): exported1,
                ("guide", None): exported2,
            },
        )
        new_project = project.upsert_export_entry("docs", None, "/new.md", "c1d2e3f4")
        assert len(new_project.exports) == 2
        assert new_project.exports[("docs", None)].path == "/new.md"
        assert new_project.exports[("guide", None)].path == "/export2.md"

    def test_upsert_export_entry_with_pattern(self):
        """Test upsert_export_entry with pattern."""
        project = Project(name="test")
        new_project = project.upsert_export_entry("docs", "*.md", "/export.md", "a3f5c8d1")
        assert ("docs", "*.md") in new_project.exports
        assert new_project.exports[("docs", "*.md")].path == "/export.md"


class TestMetadataHashComputation:
    """Tests for metadata hash computation."""

    @pytest.mark.parametrize(
        "files_setup,expected",
        [
            ("empty", None),
            ("single", lambda h: len(h) == 8),
        ],
    )
    def test_hash_computation(self, files_setup, expected, tmp_path):
        """Test hash computation for various file list scenarios."""
        from datetime import datetime

        from mcp_guide.discovery.files import FileInfo
        from mcp_guide.tools.tool_content import compute_metadata_hash

        docroot = tmp_path / "docs"
        docroot.mkdir()

        if files_setup == "empty":
            files = []
        elif files_setup == "single":
            file_path = docroot / "a.md"
            file_path.touch()
            files = [
                FileInfo(
                    path=file_path,
                    size=100,
                    content_size=100,
                    mtime=datetime.fromtimestamp(1000),
                    name="a.md",
                ),
            ]

        hash_val = compute_metadata_hash(files, docroot)
        assert expected(hash_val) if callable(expected) else hash_val == expected

    def test_same_filename_different_paths(self, tmp_path):
        """Test that files with same name in different directories produce different hashes."""
        from datetime import datetime

        from mcp_guide.discovery.files import FileInfo
        from mcp_guide.tools.tool_content import compute_metadata_hash

        docroot = tmp_path / "docs"
        docroot.mkdir()
        (docroot / "dir1").mkdir()
        (docroot / "dir2").mkdir()

        file1_path = docroot / "dir1" / "file.md"
        file2_path = docroot / "dir2" / "file.md"
        file1_path.touch()
        file2_path.touch()

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

        hash1 = compute_metadata_hash(files1, docroot)
        hash2 = compute_metadata_hash(files2, docroot)
        assert hash1 != hash2, "Files with same name in different directories must have different hashes"


class TestProjectExportsBackwardsCompatibility:
    """Tests for backwards compatibility of Project.exports field with old project configs."""

    def test_project_without_exports_field(self):
        """Test that Project can be created without exports field (backwards compatibility)."""
        # Simulate loading old config that doesn't have exports field
        project = Project(
            name="old-project",
            categories={"docs": Category(dir="docs/", patterns=["*.md"], name="docs")},
        )

        # Should have empty exports dict by default
        assert hasattr(project, "exports")
        assert project.exports == {}
        assert len(project.exports) == 0

    def test_old_config_dict_loads_correctly(self):
        """Test that old config dict (without exports) loads correctly."""
        # Simulate old config dict from YAML
        old_config = {
            "name": "legacy-project",
            "categories": {
                "guide": {
                    "dir": "guide/",
                    "patterns": ["*.md"],
                    "name": "guide",
                }
            },
        }

        # Should load without errors
        project = Project(**old_config)
        assert project.name == "legacy-project"
        assert project.exports == {}  # Default empty dict
