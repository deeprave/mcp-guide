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
from tests.conftest import call_mcp_tool


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create a server exposing the project management tool surface."""
    return mcp_server_factory(["tool_project"])


def test_set_project_requires_an_absolute_path() -> None:
    """Project binding takes a client filesystem path, never a configuration name."""
    with pytest.raises(ValidationError):
        SetCurrentProjectArgs(name="configuration-name")


def test_switch_project_accepts_a_configuration_name() -> None:
    """Configuration-only switching remains supported without a root path."""
    args = SwitchProjectArgs(name="documentation")

    assert args.name == "documentation"
    assert args.path is None


def test_switch_project_accepts_a_root_path_without_a_name() -> None:
    """A root switch may derive its configuration name from the path."""
    args = SwitchProjectArgs(path="../wybra-dev")

    assert args.name is None
    assert args.path == "../wybra-dev"


def test_switch_project_requires_exactly_one_name_or_path() -> None:
    """A switch request must select either a configuration or a new root."""
    with pytest.raises(ValidationError, match="name or path"):
        SwitchProjectArgs()
    with pytest.raises(ValidationError, match="not both"):
        SwitchProjectArgs(name="review", path="../other-project")


def test_clone_project_accepts_only_a_source_configuration() -> None:
    """Clone targets the current bound configuration and has no target argument."""
    assert CloneProjectArgs(from_project="source").from_project == "source"
    args = CloneProjectArgs(from_project="source", to_project="target")
    assert args.from_project == "source"
    assert not hasattr(args, "to_project")


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


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_switch_project_supports_name_and_root_rebinding_forms(mcp_server: Any, mode: str) -> None:
    """A retained MCP session can switch by configuration name or root path."""
    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True), mode=mode) as client:
        bound = await call_mcp_tool(
            client,
            "set_project",
            SetCurrentProjectArgs(path="/client/workspace/current"),
        )
        public_id = bound.structured_content["session_id"]
        supplied_id = public_id if mode == "2026-07-28" else None

        name_result = await call_mcp_tool(
            client,
            "switch_project",
            SwitchProjectArgs(name="review", session_id=supplied_id),
        )
        path_result = await call_mcp_tool(
            client,
            "switch_project",
            SwitchProjectArgs(path="/client/workspace/derived-root", session_id=supplied_id),
        )
        followup = await call_mcp_tool(client, "get_project", session_id=supplied_id)

    name_payload = json.loads(name_result.content[0].text)  # type: ignore[union-attr]
    path_payload = json.loads(path_result.content[0].text)  # type: ignore[union-attr]
    assert name_payload["success"] is True
    assert name_payload["value"]["project"] == "review"
    assert path_payload["success"] is True
    assert path_payload["value"]["project"] == "derived-root"
    assert name_result.structured_content["session_id"] == public_id
    assert path_result.structured_content["session_id"] == public_id
    assert followup.structured_content["value"]["project"] == "derived-root"
