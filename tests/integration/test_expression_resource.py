"""Expression-only content URIs advertised and read over the native MCP surface."""

import json

import pytest
from fastmcp import Client

from mcp_guide.cli import ServerConfig
from mcp_guide.server import create_application


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_native_expression_resource_reads_categories_collections_and_combined_content(
    tmp_path, monkeypatch, mode
):
    """Missing expression registration must not make valid content URIs unreachable."""
    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "documents"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    for category, body in (("guidelines", "Fixture guidelines"), ("rules", "Fixture rules")):
        (docroot / category).mkdir(parents=True)
        (docroot / category / "note.md").write_text(body, encoding="utf-8")
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))

    async with Client(application.server, mode=mode) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        session_id = bound.structured_content["session_id"]
        for category in ("guidelines", "rules"):
            await client.call_tool(
                "category_collection_add",
                {"args": {"type": "category", "name": category, "patterns": ["*.md"], "session_id": session_id}},
            )
        await client.call_tool(
            "category_collection_add",
            {
                "args": {
                    "type": "collection",
                    "name": "bundle",
                    "categories": ["guidelines", "rules"],
                    "session_id": session_id,
                }
            },
        )

        for expression, expected in (
            ("guidelines", ("Fixture guidelines",)),
            ("bundle", ("Fixture guidelines", "Fixture rules")),
            ("guidelines,rules", ("Fixture guidelines", "Fixture rules")),
            ("guidelines/note", ("Fixture guidelines",)),
        ):
            resource = await client.read_resource(f"guide://{expression}?session_id={session_id}")
            payload = json.loads(resource[0].text)
            assert payload["success"] is True
            assert payload["session_id"] == session_id
            for body in expected:
                assert body in payload["value"]

        templates = await client.list_resource_templates()
        assert "guide://{expression}{?session_id}" in {template.uri_template for template in templates}

        for uri in ("guide://guidelines", "guide://guidelines/note"):
            resource = await client.read_resource(uri)
            payload = json.loads(resource[0].text)
            assert payload["success"] is False
            assert payload["error_type"] == "no_project"
            assert payload["instruction"]

        # Missing identifiers cannot disturb the caller's actual bound session.
        resource = await client.read_resource(f"guide://guidelines?session_id={session_id}")
        payload = json.loads(resource[0].text)
        assert payload["success"] is True
        assert "Fixture guidelines" in payload["value"]
