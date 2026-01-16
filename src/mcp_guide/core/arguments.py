"""Base class for MCP arguments with schema generation."""

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict


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
           async def my_function(args: MyArgs, ctx: Context) -> Result[str]:
               return Result.ok(f"Hello {args.name}, age {args.age}")
           ```

        3. The decorator automatically:
           - Extracts individual fields from MyArgs for FastMCP's schema
           - Receives flat kwargs from FastMCP: {"name": "Alice", "age": 30, "ctx": <Context>}
           - Transforms them into MyArgs instance: MyArgs(name="Alice", age=30)
           - Calls your function with (args, ctx)

    Features:
    - Pydantic validation with extra='forbid' (rejects unknown fields)
    - Automatic schema markdown generation for descriptions
    - Type-safe argument access in implementations
    - Validation errors collected and returned as structured error_data
    """

    model_config = ConfigDict(extra="forbid")

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

            # Handle type
            prop_type = prop.get("type", "any")
            if "enum" in prop:
                prop_type = f"enum: {', '.join(repr(v) for v in prop['enum'])}"

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
