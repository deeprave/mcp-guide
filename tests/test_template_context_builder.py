"""Tests for template context builder functionality."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mcp_guide.utils.template_context import TemplateContext, add_file_context, build_template_context


@dataclass
class MockFileInfo:
    """Mock FileInfo for testing."""

    path: Path
    size: int
    mtime: datetime
    basename: str
    content: str | None = None
    category: str | None = None
    collection: str | None = None
    ctime: datetime | None = None


class TestBuildTemplateContext:
    """Test build_template_context function."""

    def test_build_template_context_signature(self):
        """Test build_template_context function exists with correct signature."""
        result = build_template_context()
        assert isinstance(result, TemplateContext)

    def test_layered_context_creation(self):
        """Test proper layering order: collection > category > project > agent > system."""
        # Test context layering priority (without file data)
        system_data = {"name": "SystemDefault", "timestamp": "2024-01-01"}
        project_data = {"name": "TestProject", "version": "1.0"}
        collection_data = {"name": "TestCollection", "version": "2.0"}

        context = build_template_context(
            system_data=system_data, project_data=project_data, collection_data=collection_data
        )

        # Collection should override project and system (highest priority)
        assert context["name"] == "TestCollection"
        # Collection-specific data should be available
        assert context["version"] == "2.0"
        # System should be available when not overridden
        assert context["timestamp"] == "2024-01-01"

    def test_file_context_per_file_rendering(self):
        """Test file context is added per-file using new_child."""
        # Build base context
        base_context = build_template_context(
            system_data={"name": "SystemDefault"}, project_data={"name": "TestProject"}
        )

        # Create mock FileInfo with realistic template structure
        file_info = MockFileInfo(
            path=Path("test/file.txt.mustache"),  # Actual template path
            size=1024,
            mtime=datetime(2024, 1, 1, 12, 0, 0),
            basename="test/file.txt",  # Rendered path (template extension removed)
            category="docs",
            collection="main",
        )

        # Add file context for specific file
        file_context = add_file_context(base_context, file_info)

        # Template should get the rendered path (basename), not template path
        assert file_context["path"] == "test/file.txt"  # Rendered path from basename
        assert file_context["category"] == "docs"
        assert file_context["size"] == 1024

        # Base context should remain unchanged
        assert base_context["name"] == "TestProject"

    def test_new_child_returns_template_context(self):
        """Test new_child() override returns TemplateContext instance."""
        base_context = build_template_context(system_data={"base": "value"})

        # Create child context
        child_context = base_context.new_child({"child": "value"})

        # Should return TemplateContext, not ChainMap
        assert isinstance(child_context, TemplateContext)
        # Should have access to both child and parent data
        assert child_context["child"] == "value"
        assert child_context["base"] == "value"

    def test_type_conversion_utilities(self):
        """Test type conversion for template-safe values."""
        # Test datetime and Path conversion
        test_data = {
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "file_path": Path("/test/path"),
            "count": 42,
            "active": True,
            "description": None,
        }

        context = build_template_context(system_data=test_data)

        # Should convert to strings
        assert isinstance(context["created_at"], str)
        assert isinstance(context["file_path"], str)
        # Should preserve simple types
        assert context["count"] == 42
        assert context["active"] is True
        # Should handle None values
        assert context["description"] == ""

    def test_error_handling_missing_data(self):
        """Test graceful handling of missing data sources."""
        # Should not raise errors with None/missing data
        context = build_template_context(system_data=None, project_data={})

        assert isinstance(context, TemplateContext)

    def test_error_handling_invalid_values(self):
        """Test validation for invalid context values."""
        # Should handle invalid data gracefully
        invalid_data = {
            "valid_key": "valid_value",
            123: "invalid_key",  # Non-string key
            "complex_object": object(),  # Non-serializable value
        }

        context = build_template_context(system_data=invalid_data)

        # Should only include valid entries
        assert "valid_key" in context
        assert context["valid_key"] == "valid_value"

    def test_dropped_keys_logging(self, caplog):
        """Test that dropped non-string keys are logged."""
        invalid_data = {
            "valid_key": "valid_value",
            123: "invalid_key",  # Non-string key
            (1, 2): "tuple_key",  # Non-string key
        }

        with caplog.at_level(logging.WARNING):
            context = build_template_context(system_data=invalid_data)

        # Should log warnings for dropped keys
        assert len(caplog.records) == 2
        assert "Dropping non-string key" in caplog.records[0].message
        assert "123" in caplog.records[0].message
        assert "int" in caplog.records[0].message
        assert "Dropping non-string key" in caplog.records[1].message
        assert "(1, 2)" in caplog.records[1].message
        assert "tuple" in caplog.records[1].message

        # Should only include valid entries
        assert "valid_key" in context
        assert context["valid_key"] == "valid_value"
        assert len(context) == 1

    def test_datetime_conversion_error_handling(self, caplog):
        """Test error handling for invalid datetime objects in FileInfo."""
        # Build base context
        base_context = build_template_context(system_data={"name": "SystemDefault"})

        # Create mock FileInfo with invalid datetime
        file_info = MockFileInfo(
            path=Path("test/file.txt.mustache"),
            size=1024,
            mtime="invalid_datetime",  # Invalid datetime object
            basename="test/file.txt",
            category="docs",
            ctime="invalid_ctime",  # Invalid ctime object
        )

        with caplog.at_level(logging.WARNING):
            file_context = add_file_context(base_context, file_info)

        # Should log warnings for datetime conversion errors
        assert len(caplog.records) == 2
        assert "Failed to convert file mtime to ISO format" in caplog.records[0].message
        assert "Failed to convert file ctime to ISO format" in caplog.records[1].message

        # Should still create context with empty datetime fields
        assert file_context["path"] == "test/file.txt"
        assert file_context["mtime"] == ""
        assert file_context["ctime"] == ""
        assert file_context["size"] == 1024
