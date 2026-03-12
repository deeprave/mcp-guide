"""Tests for export tracking models."""

import pytest

from mcp_guide.models.project import Category, ExportedTo, Project


class TestExportedTo:
    """Tests for ExportedTo dataclass."""

    def test_create_exported_to(self):
        """Test creating ExportedTo instance."""
        exported = ExportedTo(path="/path/to/export.md", mtime=1234567890.5)
        assert exported.path == "/path/to/export.md"
        assert exported.mtime == 1234567890.5

    def test_exported_to_immutable(self):
        """Test ExportedTo is immutable."""
        exported = ExportedTo(path="/path/to/export.md", mtime=1234567890.5)
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
        exported = ExportedTo(path="/export.md", mtime=1234567890.5)
        project = Project(
            name="test",
            exports={("docs", None): exported},
        )
        assert len(project.exports) == 1
        assert ("docs", None) in project.exports
        assert project.exports[("docs", None)].path == "/export.md"
        assert project.exports[("docs", None)].mtime == 1234567890.5

    def test_project_exports_multiple_entries(self):
        """Test Project with multiple export entries."""
        exported1 = ExportedTo(path="/export1.md", mtime=1234567890.5)
        exported2 = ExportedTo(path="/export2.md", mtime=1234567891.5)
        project = Project(
            name="test",
            exports={
                ("docs", None): exported1,
                ("docs", "*.md"): exported2,
            },
        )
        assert len(project.exports) == 2
        assert project.exports[("docs", None)].mtime == 1234567890.5
        assert project.exports[("docs", "*.md")].mtime == 1234567891.5


class TestProjectExportMethods:
    """Tests for Project export tracking methods."""

    def test_get_export_entry_not_found(self):
        """Test get_export_entry returns None when not found."""
        project = Project(name="test")
        result = project.get_export_entry("docs", None)
        assert result is None

    def test_get_export_entry_found(self):
        """Test get_export_entry returns entry when found."""
        exported = ExportedTo(path="/export.md", mtime=1234567890.5)
        project = Project(name="test", exports={("docs", None): exported})
        result = project.get_export_entry("docs", None)
        assert result is not None
        assert result.path == "/export.md"
        assert result.mtime == 1234567890.5

    def test_get_export_entry_with_pattern(self):
        """Test get_export_entry with pattern."""
        exported = ExportedTo(path="/export.md", mtime=1234567890.5)
        project = Project(name="test", exports={("docs", "*.md"): exported})
        result = project.get_export_entry("docs", "*.md")
        assert result is not None
        assert result.path == "/export.md"

    def test_upsert_export_entry_new(self):
        """Test upsert_export_entry adds new entry."""
        project = Project(name="test")
        new_project = project.upsert_export_entry("docs", None, "/export.md", 1234567890.5)
        assert len(new_project.exports) == 1
        assert ("docs", None) in new_project.exports
        assert new_project.exports[("docs", None)].path == "/export.md"
        assert new_project.exports[("docs", None)].mtime == 1234567890.5

    def test_upsert_export_entry_update(self):
        """Test upsert_export_entry updates existing entry."""
        exported = ExportedTo(path="/old.md", mtime=1234567890.5)
        project = Project(name="test", exports={("docs", None): exported})
        new_project = project.upsert_export_entry("docs", None, "/new.md", 1234567900.5)
        assert len(new_project.exports) == 1
        assert new_project.exports[("docs", None)].path == "/new.md"
        assert new_project.exports[("docs", None)].mtime == 1234567900.5

    def test_upsert_export_entry_preserves_other_entries(self):
        """Test upsert_export_entry preserves other entries."""
        exported1 = ExportedTo(path="/export1.md", mtime=1234567890.5)
        exported2 = ExportedTo(path="/export2.md", mtime=1234567891.5)
        project = Project(
            name="test",
            exports={
                ("docs", None): exported1,
                ("guide", None): exported2,
            },
        )
        new_project = project.upsert_export_entry("docs", None, "/new.md", 1234567900.5)
        assert len(new_project.exports) == 2
        assert new_project.exports[("docs", None)].path == "/new.md"
        assert new_project.exports[("guide", None)].path == "/export2.md"

    def test_upsert_export_entry_with_pattern(self):
        """Test upsert_export_entry with pattern."""
        project = Project(name="test")
        new_project = project.upsert_export_entry("docs", "*.md", "/export.md", 1234567890.5)
        assert ("docs", "*.md") in new_project.exports
        assert new_project.exports[("docs", "*.md")].path == "/export.md"


class TestExportStalenessDetection:
    """Tests for export staleness detection logic."""

    def test_max_mtime_calculation(self):
        """Test calculating max mtime from file list."""
        from datetime import datetime

        from mcp_guide.discovery.files import FileInfo

        files = [
            FileInfo(path="a.md", size=100, content_size=100, mtime=datetime.fromtimestamp(1000), name="a.md"),
            FileInfo(path="b.md", size=100, content_size=100, mtime=datetime.fromtimestamp(2000), name="b.md"),
            FileInfo(path="c.md", size=100, content_size=100, mtime=datetime.fromtimestamp(1500), name="c.md"),
        ]

        max_mtime = max(f.mtime.timestamp() for f in files)
        assert max_mtime == 2000.0

    def test_empty_file_list_max_mtime(self):
        """Test max mtime with empty file list."""
        files = []
        # Should handle empty list gracefully
        max_mtime = max((f.mtime.timestamp() for f in files), default=0.0)
        assert max_mtime == 0.0


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
