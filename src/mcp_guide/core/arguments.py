"""Base class for MCP arguments with schema generation."""

from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field

SESSION_ID_DESCRIPTION = (
    "Opaque Guide interaction identifier returned by set_project. "
    "Pass it through unchanged on later tool, prompt, and resource calls. "
    "Do not construct, alter, or treat it as a FastMCP transport session id."
)


def _schema_type_label(prop: dict[str, Any]) -> str:
    """Render a JSON Schema property as a concise advertised type label."""
    if "enum" in prop:
        return f"enum: {', '.join(repr(v) for v in prop['enum'])}"

    combined = prop.get("anyOf") or prop.get("oneOf")
    if combined:
        return " | ".join(_schema_type_label(variant) if isinstance(variant, dict) else "any" for variant in combined)

    prop_type = prop.get("type")
    if prop_type == "array":
        items = prop.get("items")
        item_label = _schema_type_label(items) if isinstance(items, dict) else "any"
        return f"array[{item_label}]"
    if prop_type == "object":
        return "object"
    if isinstance(prop_type, list):
        return " | ".join(str(part) for part in prop_type)
    if prop_type:
        return str(prop_type)
    return "any"


class Arguments(BaseModel):
    """Base class for MCP arguments with automatic schema generation and validation.

    This class provides common functionality for both tool and prompt arguments.
    It handles Pydantic validation, schema generation, and description building.

    Usage Pattern:
        1. Define your arguments class:
           ```python
           class MyArgs(Arguments):
               name: str
               age: int = 0
           ```

        2. Define your function:
           ```python
           @decorator(args_class=MyArgs)
           async def my_function(args: MyArgs, request_context: RequestContext) -> Result[str]:
               return Result.ok(f"Hello {args.name}, age {args.age}")
           ```

        3. The decorator registers the Args class as a nested ``args`` object for FastMCP.
           FastMCP receives {"args": {"name": "Alice", "age": 30}} plus injected ``ctx``.
           The wrapper builds MyArgs and calls the function with (args, request_context).

    Features:
    - Pydantic validation with extra='ignore' (unknown fields are dropped)
    - Automatic schema markdown generation for descriptions
    - Type-safe argument access in implementations
    - Validation errors collected and returned as structured error_data
    """

    model_config = ConfigDict(extra="ignore")

    session_id: Optional[str] = Field(
        default=None,
        description=SESSION_ID_DESCRIPTION,
    )

    @classmethod
    def to_schema_markdown(cls) -> str:
        """Generate markdown-formatted schema.

        Returns:
            Markdown string with argument documentation
        """
        schema = cls.model_json_schema()
        lines = ["## Arguments\n"]

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name, prop in properties.items():
            req_marker = " (required)" if name in required else ""
            prop_type = _schema_type_label(prop)

            lines.append(f"- **{name}**{req_marker}: {prop_type}")

            if "description" in prop:
                lines.append(f"  - {prop['description']}")

        return "\n".join(lines)

    @classmethod
    def build_description(cls, func: Callable[..., Any]) -> str:
        """Combine function docstring with argument schema.

        Args:
            func: Function to build description for

        Returns:
            Complete description combining docstring and schema
        """
        parts = []

        if func.__doc__:
            parts.append(func.__doc__.strip())

        # Get argument type from function signature
        import inspect

        sig = inspect.signature(func)
        for param in sig.parameters.values():
            if param.annotation != inspect.Parameter.empty:
                if isinstance(param.annotation, type) and issubclass(param.annotation, Arguments):
                    schema = param.annotation.to_schema_markdown()
                    parts.append(schema)
                    break

        return "\n\n".join(parts)
