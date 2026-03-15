"""Template lambda functions for Mustache templates."""

from collections import ChainMap
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


class SyntaxHighlighter:
    """Syntax highlighter with Pygments integration."""

    def __init__(self) -> None:
        """Initialize and check for Pygments availability."""
        self.pygments_available = self._check_pygments()

    def _check_pygments(self) -> bool:
        """Check if Pygments is available."""
        import importlib.util

        return importlib.util.find_spec("pygments") is not None


class TemplateFunctions:
    """Template lambda functions with ChainMap context integration."""

    def __init__(self, context: ChainMap[str, Any]) -> None:
        """Initialize with ChainMap context."""
        self.context = context
        self.highlighter = SyntaxHighlighter()
        self.errors: list[str] = []

    def _error(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Signal an application-level error: {{#_error}}message{{/_error}}"""
        try:
            message = render(text) if render else text
        except Exception as e:
            logger.warning("_error lambda: render failed: %s", e)
            return ""
        if message:
            self.errors.append(message)
        return ""

    def _parse_template_args(self, text: str) -> tuple[str, str]:
        """Parse mustache-style lambda body into (arg, variable_name).

        Example:
            "%Y-%m-%d{{created_at}}" -> ("%Y-%m-%d", "created_at")
        """
        if "{{" not in text or "}}" not in text:
            raise ValueError(f"Invalid template format: {text}")

        # Split once to keep everything before the first '{{' as the argument
        arg_part, remainder = text.split("{{", 1)

        # Extract content inside the first pair of braces
        if "}}" not in remainder:
            raise ValueError(f"Invalid template format: {text}")
        var_part, _ = remainder.split("}}", 1)
        var_name = var_part.strip()

        if not var_name:
            raise ValueError(f"Missing variable name in template: {text}")
        if var_name != "@" and not var_name.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError(f"Invalid variable name: {var_name}")

        return arg_part, var_name

    def format_date(self, text: str, render: Optional[Any] = None) -> str:
        """Format dates: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"""
        format_str, var_name = self._parse_template_args(text)

        if var_name not in self.context:
            raise KeyError(f"Variable not found in context: {var_name}")

        date_value = self.context[var_name]
        if not hasattr(date_value, "strftime"):
            raise TypeError(f"Variable {var_name} is not a datetime object")

        return str(date_value.strftime(format_str))

    def truncate(self, text: str, render: Optional[Any] = None) -> str:
        """Truncate with ellipses: {{#truncate}}50{{description}}{{/truncate}}"""
        length_str, var_name = self._parse_template_args(text)

        try:
            max_len = int(length_str.strip())
        except ValueError:
            raise ValueError(f"Invalid length value: {length_str}")

        if max_len < 0:
            raise ValueError(f"Length must be non-negative: {max_len}")

        if var_name not in self.context:
            raise KeyError(f"Variable not found in context: {var_name}")

        value = str(self.context[var_name])
        return value[:max_len] + "..." if len(value) > max_len else value

    def highlight_code(self, text: str, render: Optional[Any] = None) -> str:
        """Syntax highlight: {{#highlight_code}}python{{code_snippet}}{{/highlight_code}}"""
        language, var_name = self._parse_template_args(text)

        if not language.strip() or not language.replace("-", "").replace("+", "").isalnum():
            raise ValueError(f"Invalid language name: {language}")

        if var_name not in self.context:
            raise KeyError(f"Variable not found in context: {var_name}")

        code = str(self.context[var_name])
        return f"```{language}\n{code}\n```"

    def pad_right(self, text: str, render: Optional[Any] = None) -> str:
        """Pad string to fixed width: {{#pad_right}}20{{command_name}}{{/pad_right}}"""
        try:
            width_str, var_name = self._parse_template_args(text)
            width = int(width_str.strip())

            if var_name not in self.context:
                raise KeyError(f"Variable not found in context: {var_name}")

            value = str(self.context[var_name])
            return value.ljust(width)
        except ValueError as e:
            return f"[Pad Error: {e}]"

    def contains(self, text: str, render: Optional[Any] = None) -> str:
        """Check if value contains substring: {{#contains}}substring{{variable}}{{/contains}}"""
        substring, var_name = self._parse_template_args(text)

        if var_name not in self.context:
            return ""

        actual = str(self.context[var_name])
        return render(text) if render and substring.strip() in actual else ""

    def time_ago(self, text: str, render: Optional[Any] = None) -> str:
        """Format timestamp as relative time: {{#time_ago}}{{exported_at}}{{/time_ago}}"""
        _, var_name = self._parse_template_args(text)

        if var_name not in self.context:
            return ""

        value = self.context[var_name]
        if not value:
            return "unknown"
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
        else:
            raise TypeError(f"Variable {var_name} is not a numeric timestamp")

        delta = datetime.now(timezone.utc) - dt
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days}d{hours}h ago"
        elif hours > 0:
            return f"{hours}h{minutes}m ago"
        else:
            return f"{minutes}m ago"

    def _get_nested_value(self, var_name: str) -> Optional[str]:
        """Get value from context, supporting dot notation for nested keys.

        Args:
            var_name: Variable name, may include dots for nested access (e.g., "agent.class")

        Returns:
            String value if found, None otherwise
        """
        if "." not in var_name:
            return str(self.context[var_name]) if var_name in self.context else None

        parts = var_name.split(".")
        value = self.context.get(parts[0])
        for part in parts[1:]:
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return str(value) if value is not None else None

    def equals(self, text: str, render: Optional[Any] = None) -> str:
        """Compare values: {{#equals}}value{{variable}}{{/equals}}

        Returns the rendered section content if values match, empty string otherwise.
        """
        expected, var_name = self._parse_template_args(text)
        actual = self._get_nested_value(var_name)

        if actual is None or actual != expected.strip():
            return ""

        # Render section content (everything after the variable reference)
        if render:
            var_end = text.find("}}") + 2
            return str(render(text[var_end:]))
        return ""
