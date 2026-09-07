"""Actual exports track source changes, force destinations and survive session reload."""

import os

import pytest
import yaml

from mcp_guide.models import Category
from mcp_guide.tools.tool_content import ExportContentArgs, export_content
from tests.helpers import (
    bind_isolated_test_session,
    create_bound_test_session,
    request_context_for,
    tool_result_payload,
)


@pytest.mark.anyio
async def test_exports_track_real_content_changes_and_persist(runtime, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    source = docs / "readme.md"
    source.write_text("Original content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "export-tracking")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    async def export(path="output.md", *, force=False, pattern=None):
        args = ExportContentArgs(expression="docs", path=path, force=force, pattern=pattern)
        payload = tool_result_payload(await export_content.__wrapped__(args, await request_context_for(session)))
        assert payload["success"] is True
        assert "RAW FILE DATA" in payload["instruction"]
        return payload

    first = await export()
    assert first["value"].endswith("Original content")
    initial = session.project.get_export_entry("docs", None)
    assert initial.path == ".knowledge/output.md"
    assert initial.metadata_hash
    assert initial.exported_at > 0

    repeated = await export("ignored.md")
    assert repeated["value"] == first["value"]
    assert "`.knowledge/output.md`" in repeated["instruction"]
    assert session.project.get_export_entry("docs", None) == initial

    forced = await export("forced.md", force=True)
    assert forced["value"] == first["value"]
    assert "`.knowledge/forced.md`" in forced["instruction"]
    assert "overwrite if it already exists" in forced["instruction"]
    assert session.project.get_export_entry("docs", None).path == ".knowledge/forced.md"

    previous_mtime = source.stat().st_mtime
    source.write_text("Changed content")
    os.utime(source, (previous_mtime + 2, previous_mtime + 2))
    changed = await export("changed.md")
    assert changed["value"].endswith("Changed content")
    changed_entry = session.project.get_export_entry("docs", None)
    assert changed_entry.metadata_hash != initial.metadata_hash
    assert changed_entry.path == ".knowledge/changed.md"

    await export("pattern.md", pattern="*.md")
    assert session.project.get_export_entry("docs", None) == changed_entry
    assert session.project.get_export_entry("docs", "*.md").path == ".knowledge/pattern.md"
    reloaded = await bind_isolated_test_session(runtime, project_name="export-tracking")
    assert reloaded.project.exports == session.project.exports
