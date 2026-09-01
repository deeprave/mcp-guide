"""Protocol-level integration coverage for the current project tool contract."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from fastmcp.client import Client, FastMCPTransport
from pydantic import ValidationError

from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    SetCurrentProjectArgs,
    SwitchProjectArgs,
)
from tests.conftest import assert_tool_registered, call_mcp_tool


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create a server exposing the project management tool surface."""
    return mcp_server_factory(["tool_project"])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tool_name",
    ["get_project", "set_project", "switch_project", "list_projects", "clone_project"],
)
async def test_project_tools_are_registered(mcp_server: Any, tool_name: str) -> None:
    """The current project-management API is exported through MCP."""
    tool_names = [tool.name for tool in await mcp_server.list_tools()]
    assert_tool_registered(tool_names, tool_name)


def test_set_project_requires_an_absolute_path() -> None:
    """Project binding takes a client filesystem path, never a configuration name."""
    with pytest.raises(ValidationError):
        SetCurrentProjectArgs(name="configuration-name")


def test_switch_project_accepts_a_configuration_name() -> None:
    """Configuration switching remains distinct from root binding."""
    assert SwitchProjectArgs(name="documentation").name == "documentation"


def test_clone_project_accepts_only_a_source_configuration() -> None:
    """Clone targets the current bound configuration and has no target argument."""
    assert CloneProjectArgs(from_project="source").from_project == "source"
    with pytest.raises(ValidationError):
        CloneProjectArgs(from_project="source", to_project="target")


@pytest.mark.anyio
async def test_set_project_binds_a_client_root(mcp_server: Any) -> None:
    """set_project(path) binds the client root and reports its configuration."""
    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
        result = await call_mcp_tool(
            client,
            "set_project",
            SetCurrentProjectArgs(path="/client/workspace/integration-project"),
        )

    payload = json.loads(result.content[0].text)  # type: ignore[union-attr]
    assert payload["success"] is True
    assert payload["value"]["project"] == "integration-project"
