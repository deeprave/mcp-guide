"""Base class for tool arguments with schema generation."""

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict


class ToolArguments(BaseModel):
    """Base class for tool arguments.

    Provides:
    - Pydantic validation with extra='forbid'
    - Schema markdown generation for tool descriptions
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
    def build_tool_description(cls, func: Callable[..., Any]) -> str:
        """Combine function docstring with argument schema.

        Args:
            func: Tool function

        Returns:
            Complete tool description
        """
        parts = []

        if func.__doc__:
            parts.append(func.__doc__.strip())

        # Get argument type from function signature
        import inspect

        sig = inspect.signature(func)
        for param in sig.parameters.values():
            if param.annotation != inspect.Parameter.empty:
                if isinstance(param.annotation, type) and issubclass(param.annotation, ToolArguments):
                    schema = param.annotation.to_schema_markdown()
                    parts.append(schema)
                    break

        return "\n\n".join(parts)
