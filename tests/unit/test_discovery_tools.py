"""Tests for discovery tools."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tests.helpers import tool_result_payload

from mcp_guide.core import prompt_decorator, resource_decorator
from mcp_guide.core.prompt_decorator import PromptMetadata, PromptRegistration, clear_prompt_registry
from mcp_guide.core.resource_decorator import ResourceMetadata, ResourceRegistration, clear_resource_registry
from mcp_guide.core.tool_decorator import ToolMetadata, ToolRegistration
from mcp_guide.tools.tool_discovery import ListToolsArgs, list_prompts, list_resources, list_tools


def _restore_prompt_registry(original: dict) -> None:
    clear_prompt_registry()
    prompt_decorator._PROMPT_REGISTRY.update(original)


def _restore_resource_registry(original: dict) -> None:
    clear_resource_registry()
    resource_decorator._RESOURCE_REGISTRY.update(original)


def request_context() -> SimpleNamespace:
    """Return explicit application context for a decorated-handler unit test."""

    task_manager = SimpleNamespace(process_result=AsyncMock(side_effect=lambda result: result))
    return SimpleNamespace(session=SimpleNamespace(session_id=None, task_manager=task_manager))


@pytest.mark.anyio
async def test_list_tools_returns_registered_tools():
    """Test that list_tools returns all registered tools."""
    # Manually add a test tool to registry
    from mcp_guide.core.tool_decorator import _TOOL_REGISTRY

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
        result = tool_result_payload(await list_tools.__wrapped__(args, request_context()))

        assert result["success"] is True
        assert "tools" in result["value"]
        assert result["value"]["count"] > 0

        # Check that our test tool is in the list
        tool_names = [t["name"] for t in result["value"]["tools"]]
        assert "guide_test_tool" in tool_names
    finally:
        _TOOL_REGISTRY.pop("guide_test_tool", None)


@pytest.mark.anyio
async def test_list_tools_with_args_schema():
    """Test that list_tools includes argument schemas when requested."""
    from mcp_guide.core.tool_decorator import _TOOL_REGISTRY

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
        result = tool_result_payload(await list_tools.__wrapped__(args, request_context()))

        assert result["success"] is True
        tools_with_args = [t for t in result["value"]["tools"] if "args_schema" in t]
        assert len(tools_with_args) > 0
    finally:
        _TOOL_REGISTRY.pop("guide_test_tool", None)


@pytest.mark.anyio
async def test_list_prompts_returns_registered_prompts():
    """Test that list_prompts returns all registered prompts."""
    from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY

    # Manually add a test prompt to registry
    async def test_prompt() -> str:
        return "Test prompt"

    metadata = PromptMetadata(name="test_prompt", func=test_prompt, description="Test prompt")
    _PROMPT_REGISTRY["test_prompt"] = PromptRegistration(metadata=metadata, registered=True)

    try:
        from mcp_guide.tools.tool_discovery import ListPromptsArgs

        args = ListPromptsArgs()
        result = tool_result_payload(await list_prompts.__wrapped__(args, request_context()))

        assert result["success"] is True
        assert "prompts" in result["value"]
        assert result["value"]["count"] > 0

        # Check that test prompt is in the list
        prompt_names = [p["name"] for p in result["value"]["prompts"]]
        assert "test_prompt" in prompt_names
    finally:
        _PROMPT_REGISTRY.pop("test_prompt", None)


@pytest.mark.anyio
async def test_list_resources_returns_registered_resources():
    """Test that list_resources returns all registered resources."""
    from mcp_guide.core.resource_decorator import _RESOURCE_REGISTRY

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
        result = tool_result_payload(await list_resources.__wrapped__(args, request_context()))

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
        _RESOURCE_REGISTRY.pop("test_resource", None)


def test_register_prompts_uses_prompt_name_override():
    """Prompt registration should respect MCP_PROMPT_NAME for the guide prompt."""
    from mcp_guide.core.prompt_decorator import (
        _PROMPT_REGISTRY,
        register_prompts,
    )

    original = dict(_PROMPT_REGISTRY)
    clear_prompt_registry()

    async def guide() -> str:
        return "prompt"

    metadata = PromptMetadata(name="guide", func=guide, description="Guide prompt")
    _PROMPT_REGISTRY["guide"] = PromptRegistration(metadata=metadata, registered=False)

    mcp = MagicMock()
    prompt_decorator = MagicMock()
    mcp.prompt.return_value = prompt_decorator

    try:
        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "g"}):
            register_prompts(mcp)

        mcp.prompt.assert_called_once_with(name="g")
        prompt_decorator.assert_called_once_with(guide)
    finally:
        _restore_prompt_registry(original)


def test_register_prompts_is_idempotent_for_the_same_server():
    """Prompt registration keeps a weak reference to the actual server."""
    from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY, register_prompts

    original = dict(_PROMPT_REGISTRY)
    clear_prompt_registry()

    async def guide() -> str:
        return "prompt"

    _PROMPT_REGISTRY["guide"] = PromptRegistration(
        metadata=PromptMetadata(name="guide", func=guide, description="Guide prompt"), registered=False
    )
    mcp = MagicMock()

    try:
        register_prompts(mcp)
        register_prompts(mcp)

        mcp.prompt.assert_called_once_with(name="guide")
    finally:
        _restore_prompt_registry(original)


def test_register_resources_is_idempotent_for_the_same_server():
    """Resource registration keeps a weak reference to the actual server."""
    from mcp_guide.core.resource_decorator import _RESOURCE_REGISTRY, register_resources

    original = dict(_RESOURCE_REGISTRY)
    clear_resource_registry()

    async def resource() -> str:
        return "resource"

    _RESOURCE_REGISTRY["resource"] = ResourceRegistration(
        metadata=ResourceMetadata(name="resource", uri_template="guide://resource", func=resource, description=None),
        registered=False,
    )
    mcp = MagicMock()

    try:
        register_resources(mcp)
        register_resources(mcp)

        mcp.resource.assert_called_once_with("guide://resource")
    finally:
        _restore_resource_registry(original)


def test_register_prompts_uses_default_guide_name_without_override():
    """Guide prompt should register under its own name when no override is set."""
    from mcp_guide.core.prompt_decorator import (
        _PROMPT_REGISTRY,
        register_prompts,
    )

    original = dict(_PROMPT_REGISTRY)
    clear_prompt_registry()

    async def guide() -> str:
        return "prompt"

    metadata = PromptMetadata(name="guide", func=guide, description="Guide prompt")
    _PROMPT_REGISTRY["guide"] = PromptRegistration(metadata=metadata, registered=False)

    mcp = MagicMock()
    prompt_decorator = MagicMock()
    mcp.prompt.return_value = prompt_decorator

    try:
        with patch.dict("os.environ", {}, clear=True):
            register_prompts(mcp)

        mcp.prompt.assert_called_once_with(name="guide")
        prompt_decorator.assert_called_once_with(guide)
    finally:
        _restore_prompt_registry(original)


def test_register_prompts_keeps_non_guide_prompt_name():
    """Non-guide prompts should ignore MCP_PROMPT_NAME overrides."""
    from mcp_guide.core.prompt_decorator import (
        _PROMPT_REGISTRY,
        register_prompts,
    )

    original = dict(_PROMPT_REGISTRY)
    clear_prompt_registry()

    async def status() -> str:
        return "prompt"

    metadata = PromptMetadata(name="status", func=status, description="Status prompt")
    _PROMPT_REGISTRY["status"] = PromptRegistration(metadata=metadata, registered=False)

    mcp = MagicMock()
    prompt_decorator = MagicMock()
    mcp.prompt.return_value = prompt_decorator

    try:
        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "g"}):
            register_prompts(mcp)

        mcp.prompt.assert_called_once_with(name="status")
        prompt_decorator.assert_called_once_with(status)
    finally:
        _restore_prompt_registry(original)
