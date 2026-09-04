"""Discovery tools for introspecting available MCP tools, prompts, and resources."""

from typing import Any

from pydantic import Field

from mcp_guide.core.prompt_decorator import get_prompt_registry
from mcp_guide.core.resource_decorator import get_resource_registry
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import get_tool_registry, toolfunc
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_result import ToolResult, tool_result


class ListToolsArgs(ToolArguments):
    """Arguments for list_tools."""

    include_args: bool = Field(default=False, description="Include argument schemas in output")


class ListPromptsArgs(ToolArguments):
    """Arguments for list_prompts."""

    ...


class ListResourcesArgs(ToolArguments):
    """Arguments for list_resources."""

    ...


@toolfunc(ListToolsArgs, requires_project=False)
async def list_tools(args: ListToolsArgs, request_context: RequestContext) -> ToolResult:
    """List all registered MCP tools.

    Returns tool names, descriptions, and optionally argument schemas. Does not require
    a bound project. Set include_args=True to include each tool's argument schema.
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
                tool_info["args_schema"] = registration.metadata.args_class.model_json_schema()  # ty: ignore[call-non-callable]

        tools.append(tool_info)

    return await tool_result(
        "list_tools",
        Result.ok({"tools": tools, "count": len(tools)}),
        session=request_context.session,
        session_id=args.session_id,
    )


@toolfunc(ListPromptsArgs, requires_project=False)
async def list_prompts(args: ListPromptsArgs, request_context: RequestContext) -> ToolResult:
    """List all registered MCP prompts.

    Returns prompt names and descriptions. Does not require a bound project.
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

    from mcp_guide.tools.tool_result import tool_result

    return await tool_result(
        "list_prompts",
        Result.ok({"prompts": prompts, "count": len(prompts)}),
        session=request_context.session,
        session_id=args.session_id,
    )


@toolfunc(ListResourcesArgs, requires_project=False)
async def list_resources(args: ListResourcesArgs, request_context: RequestContext) -> ToolResult:
    """List all registered MCP resources.

    Returns resource names, URI templates, and descriptions. Does not require a bound project.
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

    from mcp_guide.tools.tool_result import tool_result

    return await tool_result(
        "list_resources",
        Result.ok({"resources": resources, "count": len(resources)}),
        session=request_context.session,
        session_id=args.session_id,
    )
