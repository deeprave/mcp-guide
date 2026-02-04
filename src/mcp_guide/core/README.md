# Deferred Registration Pattern

## Overview
MCP tools, prompts, and resources use deferred registration to enable introspection and avoid import-time side effects.

## Pattern

### Tools
```python
from mcp_guide.core.tool_decorator import toolfunc

@toolfunc(ArgsClass)
async def my_tool(args: ArgsClass, ctx=None) -> str:
    return Result.ok(data).to_json_str()
```

### Prompts
```python
from mcp_guide.core.prompt_decorator import promptfunc

@promptfunc()
async def my_prompt(arg1: str = None, ctx=None):
    return "prompt content"
```

### Resources
```python
from mcp_guide.core.resource_decorator import resourcefunc

@resourcefunc("scheme://{param}")
async def my_resource(param: str, ctx=None) -> str:
    return "resource content"
```

## Registration
Decorators store metadata in registries without registering with MCP. Registration happens during server initialization:

```python
from mcp_guide.core.tool_decorator import register_tools
from mcp_guide.core.prompt_decorator import register_prompts
from mcp_guide.core.resource_decorator import register_resources

register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)
```

## Discovery
Use discovery tools to introspect available capabilities:
- `guide_list_tools` - List all registered tools
- `guide_list_prompts` - List all registered prompts
- `guide_list_resources` - List all registered resources

## Registries
- `_TOOL_REGISTRY` in `tool_decorator.py`
- `_PROMPT_REGISTRY` in `prompt_decorator.py`
- `_RESOURCE_REGISTRY` in `resource_decorator.py`

Each registry maps name → Registration object containing metadata and registration status.

## Preserved Functionality
- Logging: TRACE/DEBUG/ERROR at invocation
- Prefixing: `MCP_TOOL_PREFIX` environment variable
- Validation: Pydantic validation with error handling
- Callbacks: `on_tool()` called at tool start
