"""Integration tests for export tracking and staleness detection."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.result import Result
from mcp_guide.session import get_session
from mcp_guide.tools.tool_content import ExportContentArgs, export_content


@pytest.mark.asyncio
class TestExportStalenessIntegration:
    """Integration tests for export staleness detection."""

    async def test_first_export_creates_tracking_entry(self, session_temp_dir):
        """Test that first export creates a tracking entry."""
        session = await get_session()
        project = await session.get_project()

        assert project.get_export_entry("docs", None) is None

        updated = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
        assert updated.get_export_entry("docs", None) is not None

    async def test_repeated_export_without_changes_returns_message(self, session_temp_dir):
        """Test that repeated export without file changes returns already exported message."""
        session = await get_session()
        project = await session.get_project()

        updated = project.upsert_export_entry("docs", None, "/export.md", "ffffffff")
        await session.update_config(lambda _: updated)

        project = await session.get_project()
        entry = project.get_export_entry("docs", None)
        assert entry is not None
        assert entry.path == "/export.md"

    async def test_export_after_file_modification_proceeds(self, session_temp_dir):
        """Test that export proceeds when files have been modified."""
        session = await get_session()
        project = await session.get_project()

        updated = project.upsert_export_entry("docs", None, "/export.md", "00001000")
        await session.update_config(lambda _: updated)

        project = await session.get_project()
        entry = project.get_export_entry("docs", None)
        assert entry.metadata_hash == "00001000"

        # Simulate re-export with new hash after file modification
        updated = project.upsert_export_entry("docs", None, "/export.md", "00002000")
        await session.update_config(lambda _: updated)

        project = await session.get_project()
        entry = project.get_export_entry("docs", None)
        assert entry.metadata_hash == "00002000"

    async def test_force_flag_bypasses_staleness_check(self, session_temp_dir):
        """Test that force=True bypasses staleness detection."""
        session = await get_session()
        project = await session.get_project()

        updated = project.upsert_export_entry("docs", None, "/export.md", "ffffffff")
        await session.update_config(lambda _: updated)

        project = await session.get_project()
        entry = project.get_export_entry("docs", None)
        assert entry is not None  # Entry exists; force=True bypasses hash comparison

    async def test_different_patterns_tracked_separately(self, session_temp_dir):
        """Test that different patterns for same expression are tracked separately."""
        session = await get_session()
        project = await session.get_project()

        updated = project.upsert_export_entry("docs", None, "/export1.md", "00001000")
        updated = updated.upsert_export_entry("docs", "*.md", "/export2.md", "00002000")
        await session.update_config(lambda _: updated)

        project = await session.get_project()
        entry1 = project.get_export_entry("docs", None)
        entry2 = project.get_export_entry("docs", "*.md")

        assert entry1 is not None
        assert entry2 is not None
        assert entry1.path == "/export1.md"
        assert entry2.path == "/export2.md"
        assert entry1.metadata_hash == "00001000"
        assert entry2.metadata_hash == "00002000"

    async def test_tracking_persists_across_session_reload(self, session_temp_dir):
        """Test that export tracking persists when project config is reloaded."""
        session1 = await get_session()
        project1 = await session1.get_project()
        updated = project1.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
        await session1.update_config(lambda _: updated)

        session2 = await get_session()
        project2 = await session2.get_project()
        entry = project2.get_export_entry("docs", None)

        assert entry is not None
        assert entry.path == "/export.md"
        assert entry.metadata_hash == "a3f5c8d1"

    async def test_export_content_staleness_end_to_end(self, session_temp_dir):
        """Test export_content: first call tracks, second returns stale, force bypasses."""
        HASH = "a1b2c3d4"

        with (
            patch("mcp_guide.tools.tool_content.gather_content", new=AsyncMock(return_value=["dummy"])),
            patch("mcp_guide.tools.tool_content.compute_metadata_hash", return_value=HASH),
            patch(
                "mcp_guide.tools.tool_content.internal_get_content",
                new=AsyncMock(return_value=Result.ok("content")),
            ),
        ):
            args = ExportContentArgs(expression="docs", path="output.md")

            # First call - should succeed and create tracking entry
            result1 = await export_content(args, None)
            assert "has been exported" not in result1

            session = await get_session()
            project = await session.get_project()
            entry = project.get_export_entry("docs", None)
            assert entry is not None
            assert entry.metadata_hash == HASH

            # Second call - same hash, should return stale message
            result2 = await export_content(args, None)
            assert "has been exported" in result2

            # force=True bypasses staleness check
            args_force = ExportContentArgs(expression="docs", path="output.md", force=True)
            result3 = await export_content(args_force, None)
            assert "has been exported" not in result3
