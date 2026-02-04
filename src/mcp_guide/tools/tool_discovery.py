"""Discovery tools for introspecting available MCP tools, prompts, and resources."""

from typing import Any, Optional

from pydantic import Field

from mcp_guide.core.prompt_decorator import get_prompt_registry
from mcp_guide.core.resource_decorator import get_resource_registry
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import get_tool_registry, toolfunc
from mcp_guide.result import Result

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class ListToolsArgs(ToolArguments):
    """Arguments for list_tools."""

    include_args: bool = Field(default=False, description="Include argument schemas in output")


class ListPromptsArgs(ToolArguments):
    """Arguments for list_prompts."""

    ...


class ListResourcesArgs(ToolArguments):
    """Arguments for list_resources."""

    ...


@toolfunc(ListToolsArgs)
async def list_tools(args: ListToolsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all registered MCP tools.

    Returns tool names, descriptions, and optionally argument schemas.

    Args:
        args: List tools arguments
        ctx: MCP context

    Returns:
        Result with list of tools
    """
    tools = []
    for tool_name, registration in get_tool_registry().items():
        tool_info: dict[str, Any] = {
            "name": registration.metadata.name,
            "description": registration.metadata.description,
            "registered": registration.registered,
        }

        if args.include_args and registration.metadata.args_class:
            # Get schema from Pydantic model
            if hasattr(registration.metadata.args_class, "model_json_schema"):
                tool_info["args_schema"] = registration.metadata.args_class.model_json_schema()

        tools.append(tool_info)

    return Result.ok({"tools": tools, "count": len(tools)}).to_json_str()


@toolfunc(ListPromptsArgs)
async def list_prompts(args: ListPromptsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all registered MCP prompts.

    Returns prompt names and descriptions.

    Args:
        args: List prompts arguments
        ctx: MCP context

    Returns:
        Result with list of prompts
    """
    prompts = []
    for prompt_name, registration in get_prompt_registry().items():
        prompts.append(
            {
                "name": registration.metadata.name,
                "description": registration.metadata.description,
                "registered": registration.registered,
            }
        )

    return Result.ok({"prompts": prompts, "count": len(prompts)}).to_json_str()


@toolfunc(ListResourcesArgs)
async def list_resources(args: ListResourcesArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all registered MCP resources.

    Returns resource names, URI templates, and descriptions.

    Args:
        args: List resources arguments
        ctx: MCP context

    Returns:
        Result with list of resources
    """
    resources = []
    for resource_name, registration in get_resource_registry().items():
        resources.append(
            {
                "name": registration.metadata.name,
                "uri_template": registration.metadata.uri_template,
                "description": registration.metadata.description,
                "registered": registration.registered,
            }
        )

    return Result.ok({"resources": resources, "count": len(resources)}).to_json_str()
