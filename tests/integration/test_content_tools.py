"""Legacy MCP content retrieval through real project binding and configuration."""

import pytest
import yaml
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.tools.tool_content import ContentArgs
from mcp_guide.tools.tool_project import SetCurrentProjectArgs
from mcp_guide.utils.project_hash import calculate_project_hash, generate_project_key
from tests.conftest import call_mcp_tool


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    return mcp_server_factory(["tool_content", "tool_project"])


@pytest.mark.anyio
async def test_legacy_content_retrieval_combines_filters_and_deduplicates(mcp_server, runtime, tmp_path):
    root = tmp_path / "content-test"
    root_hash = calculate_project_hash(str(root))
    key = generate_project_key("content-test", root_hash)
    config = runtime.configuration_service().config_file
    docroot = config.parent / "docs"
    for folder in ("guide", "lang", "context", "empty"):
        (docroot / folder).mkdir(parents=True, exist_ok=True)
    (docroot / "guide/guidelines.md").write_text("Project Guidelines")
    (docroot / "lang/python.md").write_text("Python Guide")
    (docroot / "context/jira.md").write_text("Jira Integration")
    (docroot / "context/settings.yaml").write_text("Unwanted YAML content")
    project = {
        "name": "content-test",
        "hash": root_hash,
        "categories": {
            name: {"dir": name, "patterns": ["*.md", "*.yaml"]} for name in ("guide", "lang", "context", "empty")
        },
        "collections": {
            "guide": {"categories": ["guide"]},
            "docs": {"categories": ["guide"]},
            "all": {"categories": ["docs", "lang"]},
            "col1": {"categories": ["guide", "col2"]},
            "col2": {"categories": ["lang", "col1"]},
        },
    }
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {key: project}}))
    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode="legacy") as client:
        bound = await call_mcp_tool(client, "set_project", SetCurrentProjectArgs(path=str(root)))
        assert bound.structured_content["success"] is True

        async def read(expression, pattern=None):
            response = await call_mcp_tool(client, "get_content", ContentArgs(expression=expression, pattern=pattern))
            payload = response.structured_content
            assert payload["success"] is True
            return payload

        assert (await read("lang"))["value"] == "Python Guide"
        assert (await read("guide"))["value"] == "Project Guidelines"
        for expression in ("all", "col1"):
            content = (await read(expression))["value"]
            assert content.count("Project Guidelines") == 1
            assert content.count("Python Guide") == 1
        assert (await read("context", "*.md"))["value"] == "Jira Integration"
        empty = await read("empty")
        assert empty["value"] == "No matching content found for 'empty'"
        assert empty["instruction"]
