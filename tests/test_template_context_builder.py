"""Tests for template context builder functionality."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mcp_guide.utils.template_context import (
    TemplateContext,
    add_file_context,
    build_template_context,
    get_transient_context,
)


@dataclass
class MockFileInfo:
    """Mock FileInfo for testing."""

    path: Path
    size: int
    mtime: datetime
    name: str
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
        # Test context layering priority across all levels (without file data)
        system_data = {
            "name": "SystemDefault",
            "timestamp": "2024-01-01",
            "priority_key": "system",
            "system_only": "system-only",
        }
        agent_data = {
            "name": "AgentDefault",
            "priority_key": "agent",
            "agent_only": "agent-only",
        }
        project_data = {
            "name": "ProjectDefault",
            "version": "1.0",
            "priority_key": "project",
            "project_only": "project-only",
        }
        category_data = {
            "name": "CategoryDefault",
            "priority_key": "category",
            "category_only": "category-only",
        }
        collection_data = {
            "name": "CollectionDefault",
            "version": "2.0",
            "priority_key": "collection",
            "collection_only": "collection-only",
        }

        context = build_template_context(
            system_data=system_data,
            agent_data=agent_data,
            project_data=project_data,
            category_data=category_data,
            collection_data=collection_data,
        )

        # Keys defined at all levels should resolve according to:
        # collection > category > project > agent > system
        assert context["name"] == "CollectionDefault"
        assert context["priority_key"] == "collection"

        # Keys unique to each level should be preserved in the merged context
        assert context["collection_only"] == "collection-only"
        assert context["category_only"] == "category-only"
        assert context["project_only"] == "project-only"
        assert context["agent_only"] == "agent-only"
        assert context["system_only"] == "system-only"

        # Non-overlapping keys from lower-precedence levels should not be overridden
        assert context["timestamp"] == "2024-01-01"
        assert context["version"] == "2.0"

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
            name="test/file.txt",  # Rendered path (template extension removed)
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

    def test_error_handling_non_mapping_inputs(self):
        """Test that non-mapping inputs are treated as empty data."""
        # Non-dict system_data should be treated as empty
        context = build_template_context(system_data=[("key", "value")], project_data=None)

        assert isinstance(context, TemplateContext)
        assert len(context) == 0
        # Ensure no unexpected keys are added
        assert list(context) == []

        # Non-dict project_data should also be treated as empty
        context = build_template_context(system_data=None, project_data="not-a-dict")

        assert isinstance(context, TemplateContext)
        assert len(context) == 0
        assert list(context) == []

    def test_error_handling_invalid_values(self):
        """Test validation for invalid context values."""
        # Should handle invalid data gracefully
        invalid_data = {
            "valid_key": "valid_value",
            123: "invalid_key",  # Non-string key
            "complex_object": object(),  # Non-serializable value
        }

        context = build_template_context(system_data=invalid_data)

        # Valid entries should be preserved
        assert "valid_key" in context
        assert context["valid_key"] == "valid_value"

        # Non-string keys should be dropped
        assert 123 not in context

        # Complex/non-serializable values should be retained and converted to strings
        assert "complex_object" in context
        assert isinstance(context["complex_object"], str)

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
            name="test/file.txt",
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

    def test_get_transient_context(self):
        """Test get_transient_context adds fresh runtime data."""
        # Build base context
        base_context = build_template_context(system_data={"static": "value"})

        # Get transient context
        transient_context = get_transient_context(base_context)

        # Should have transient data
        assert "now" in transient_context
        assert "timestamp" in transient_context
        assert "static" in transient_context  # Base context still accessible

        # Should be fresh timestamps
        assert isinstance(transient_context["now"], str)
        assert isinstance(transient_context["timestamp"], int)

        # Timestamps should be recent (within last few seconds)
        now_timestamp = int(time.time())
        assert abs(transient_context["timestamp"] - now_timestamp) < 5

        # Should be TemplateContext instance
        assert isinstance(transient_context, TemplateContext)
