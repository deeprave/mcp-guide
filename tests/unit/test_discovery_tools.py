"""Discovery payloads and deferred registration on real MCP servers."""

from types import SimpleNamespace

import pytest
from fastmcp import FastMCP
from tests.helpers import tool_result_payload

from mcp_guide.core import prompt_decorator, resource_decorator, tool_decorator
from mcp_guide.core.prompt_decorator import PromptMetadata, PromptRegistration, register_prompts
from mcp_guide.core.resource_decorator import ResourceMetadata, ResourceRegistration, register_resources
from mcp_guide.core.tool_decorator import ToolMetadata, ToolRegistration
from mcp_guide.tools.tool_discovery import (
    ListPromptsArgs,
    ListResourcesArgs,
    ListToolsArgs,
    list_prompts,
    list_resources,
    list_tools,
)


@pytest.fixture
def isolated_registries(monkeypatch):
    for module, names in (
        (tool_decorator, ("_TOOL_REGISTRY", "_REGISTERED_TOOL_SERVERS")),
        (prompt_decorator, ("_PROMPT_REGISTRY", "_REGISTERED_PROMPT_SERVERS")),
        (resource_decorator, ("_RESOURCE_REGISTRY", "_REGISTERED_RESOURCE_SERVERS")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, {})


async def example() -> str:
    return "Example content"


@pytest.mark.anyio
async def test_tool_discovery_returns_exact_metadata_and_optional_schema(isolated_registries):
    context = SimpleNamespace(session=None)
    empty = tool_result_payload(await list_tools.__wrapped__(ListToolsArgs(), context))
    assert empty["success"]
    assert empty["value"] == {"tools": [], "count": 0}
    for name, args_class, registered in (("with_args", ListToolsArgs, True), ("without_args", None, False)):
        tool_decorator._TOOL_REGISTRY[name] = ToolRegistration(
            ToolMetadata(name, example, "Description", args_class, None, example), registered=registered
        )
    expected = [
        {"name": "with_args", "description": "Description", "registered": True},
        {"name": "without_args", "description": "Description", "registered": False},
    ]
    for include_args in (False, True):
        result = tool_result_payload(await list_tools.__wrapped__(ListToolsArgs(include_args=include_args), context))
        if include_args:
            expected[0]["args_schema"] = ListToolsArgs.model_json_schema()
        assert result["success"]
        assert result["value"] == {"tools": expected, "count": 2}


@pytest.mark.anyio
async def test_prompt_and_resource_discovery_returns_exact_metadata(isolated_registries):
    context = SimpleNamespace(session=None)
    prompt_decorator._PROMPT_REGISTRY["example"] = PromptRegistration(
        PromptMetadata("example", example, "Prompt description"), registered=True
    )
    resource_decorator._RESOURCE_REGISTRY["example"] = ResourceRegistration(
        ResourceMetadata("example", "test://{collection}", example, "Resource description"), registered=False
    )
    prompts = tool_result_payload(await list_prompts.__wrapped__(ListPromptsArgs(), context))
    assert prompts["success"]
    assert prompts["value"] == {
        "prompts": [{"name": "example", "description": "Prompt description", "registered": True}],
        "count": 1,
    }
    resources = tool_result_payload(await list_resources.__wrapped__(ListResourcesArgs(), context))
    assert resources["success"]
    assert resources["value"] == {
        "resources": [
            {
                "name": "example",
                "uri_template": "test://{collection}",
                "description": "Resource description",
                "registered": False,
            }
        ],
        "count": 1,
    }


@pytest.mark.anyio
@pytest.mark.parametrize("override", [None, "g"])
async def test_prompt_names_and_registration_are_per_server(isolated_registries, monkeypatch, override):
    if override is None:
        monkeypatch.delenv("MCP_PROMPT_NAME", raising=False)
    else:
        monkeypatch.setenv("MCP_PROMPT_NAME", override)
    registry = prompt_decorator._PROMPT_REGISTRY
    for name in ("guide", "status"):
        registry[name] = PromptRegistration(PromptMetadata(name, example, "Prompt"))
    first = FastMCP("first")
    register_prompts(first)
    expected = {override or "guide", "status"}
    assert {prompt.name for prompt in await first.list_prompts()} == expected
    assert all(entry.registered for entry in registry.values())
    registry["later"] = PromptRegistration(PromptMetadata("later", example, "Later"))
    register_prompts(first)
    assert {prompt.name for prompt in await first.list_prompts()} == expected
    second = FastMCP("second")
    register_prompts(second)
    assert {prompt.name for prompt in await second.list_prompts()} == expected | {"later"}


@pytest.mark.anyio
async def test_resource_registration_is_per_server(isolated_registries):
    registry = resource_decorator._RESOURCE_REGISTRY
    registry["example"] = ResourceRegistration(ResourceMetadata("example", "guide://example", example, None))
    first = FastMCP("first")
    register_resources(first)
    assert {str(resource.uri) for resource in await first.list_resources()} == {"guide://example"}
    assert registry["example"].registered
    registry["later"] = ResourceRegistration(ResourceMetadata("later", "guide://later", example, None))
    register_resources(first)
    assert {str(resource.uri) for resource in await first.list_resources()} == {"guide://example"}
    second = FastMCP("second")
    register_resources(second)
    assert {str(resource.uri) for resource in await second.list_resources()} == {"guide://example", "guide://later"}
