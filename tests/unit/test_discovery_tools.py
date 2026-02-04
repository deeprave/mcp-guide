"""Tests for discovery tools."""

import json

import pytest

from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY, PromptMetadata, PromptRegistration
from mcp_guide.core.resource_decorator import _RESOURCE_REGISTRY, ResourceMetadata, ResourceRegistration
from mcp_guide.core.tool_decorator import _TOOL_REGISTRY, ToolMetadata, ToolRegistration
from mcp_guide.tools.tool_discovery import ListToolsArgs, list_prompts, list_resources, list_tools


@pytest.mark.anyio
async def test_list_tools_returns_registered_tools():
    """Test that list_tools returns all registered tools."""

    # Manually add a test tool to registry
    async def test_tool(ctx=None) -> str:
        return '{"success": true}'

    metadata = ToolMetadata(
        name="guide_test_tool",
        func=test_tool,
        description="Test tool",
        args_class=None,
        prefix="guide",
        wrapped_func=test_tool,
    )
    _TOOL_REGISTRY["guide_test_tool"] = ToolRegistration(metadata=metadata, registered=True)

    try:
        args = ListToolsArgs(include_args=False)
        result_str = await list_tools(args)
        result = json.loads(result_str)

        assert result["success"] is True
        assert "tools" in result["value"]
        assert result["value"]["count"] > 0

        # Check that our test tool is in the list
        tool_names = [t["name"] for t in result["value"]["tools"]]
        assert "guide_test_tool" in tool_names
    finally:
        _TOOL_REGISTRY.clear()


@pytest.mark.anyio
async def test_list_tools_with_args_schema():
    """Test that list_tools includes argument schemas when requested."""

    # Add tool with args_class
    async def test_tool(args, ctx=None) -> str:
        return '{"success": true}'

    metadata = ToolMetadata(
        name="guide_test_tool",
        func=test_tool,
        description="Test tool",
        args_class=ListToolsArgs,
        prefix="guide",
        wrapped_func=test_tool,
    )
    _TOOL_REGISTRY["guide_test_tool"] = ToolRegistration(metadata=metadata, registered=True)

    try:
        args = ListToolsArgs(include_args=True)
        result_str = await list_tools(args)
        result = json.loads(result_str)

        assert result["success"] is True
        tools_with_args = [t for t in result["value"]["tools"] if "args_schema" in t]
        assert len(tools_with_args) > 0
    finally:
        _TOOL_REGISTRY.clear()


@pytest.mark.anyio
async def test_list_prompts_returns_registered_prompts():
    """Test that list_prompts returns all registered prompts."""

    # Manually add a test prompt to registry
    async def test_prompt() -> str:
        return "Test prompt"

    metadata = PromptMetadata(name="test_prompt", func=test_prompt, description="Test prompt")
    _PROMPT_REGISTRY["test_prompt"] = PromptRegistration(metadata=metadata, registered=True)

    try:
        from mcp_guide.tools.tool_discovery import ListPromptsArgs

        args = ListPromptsArgs()
        result_str = await list_prompts(args)
        result = json.loads(result_str)

        assert result["success"] is True
        assert "prompts" in result["value"]
        assert result["value"]["count"] > 0

        # Check that test prompt is in the list
        prompt_names = [p["name"] for p in result["value"]["prompts"]]
        assert "test_prompt" in prompt_names
    finally:
        _PROMPT_REGISTRY.clear()


@pytest.mark.anyio
async def test_list_resources_returns_registered_resources():
    """Test that list_resources returns all registered resources."""

    # Manually add a test resource to registry
    async def test_resource(collection: str) -> str:
        return "Test resource"

    metadata = ResourceMetadata(
        name="test_resource",
        uri_template="test://{collection}",
        func=test_resource,
        description="Test resource",
    )
    _RESOURCE_REGISTRY["test_resource"] = ResourceRegistration(metadata=metadata, registered=True)

    try:
        from mcp_guide.tools.tool_discovery import ListResourcesArgs

        args = ListResourcesArgs()
        result_str = await list_resources(args)
        result = json.loads(result_str)

        assert result["success"] is True
        assert "resources" in result["value"]
        assert result["value"]["count"] > 0

        # Check that test resource is in the list
        resource_names = [r["name"] for r in result["value"]["resources"]]
        assert "test_resource" in resource_names

        # Check URI template is included
        test_res = next(r for r in result["value"]["resources"] if r["name"] == "test_resource")
        assert "uri_template" in test_res
        assert test_res["uri_template"] == "test://{collection}"
    finally:
        _RESOURCE_REGISTRY.clear()
