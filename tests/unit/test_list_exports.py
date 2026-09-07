"""Export listings reflect real source metadata and filter tracked destinations."""

import pytest
import yaml
from tests.helpers import create_bound_test_session, request_context_for, tool_result_payload

from mcp_guide.content.gathering import gather_content
from mcp_guide.models import Category
from mcp_guide.tools.tool_content import ListExportsArgs, compute_metadata_hash, list_exports


@pytest.mark.anyio
async def test_export_listing_metadata_staleness_and_filters(runtime, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "readme.md").write_text("Source content")
    config = runtime.configuration_service().config_file
    config.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "exports")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    async def listing(glob=None):
        result = await list_exports.__wrapped__(ListExportsArgs(glob=glob), await request_context_for(session))
        payload = tool_result_payload(result)
        assert payload["success"] is True
        return payload["value"]

    assert await listing() == []
    context = await request_context_for(session)
    files = await gather_content(context, session.project, "docs")
    current_hash = compute_metadata_hash(files)
    assert current_hash is not None
    destination = tmp_path / "export.md"
    timestamp = 1234567890.0
    await session.update_config(
        lambda p: (
            p.upsert_export_entry("docs", None, str(destination), current_hash, exported_at=timestamp)
            .upsert_export_entry("docs", "*.md", str(tmp_path / "stale.md"), "different")
            .upsert_export_entry("missing", "*.py", str(tmp_path / "other" / "missing.md"), "unknown")
        )
    )
    exports = await listing()
    assert exports[0] == {
        "expression": "docs",
        "pattern": None,
        "file": "export.md",
        "path": str(tmp_path),
        "dest": str(destination),
        "exported_at": timestamp,
        "stale_state": "ok",
    }
    assert [item["stale_state"] for item in exports] == ["ok", "stale", "unknown"]
    assert await listing("DOC*") == exports[:2]
    assert await listing("*/other/*") == exports[2:]
    assert await listing("*.py") == exports[2:]
