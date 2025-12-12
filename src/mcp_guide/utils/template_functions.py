"""Template lambda functions for Mustache templates."""

from collections import ChainMap
from typing import Any, Optional


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

    def format_date(self, text: str, render: Optional[Any] = None) -> str:
        """Format dates: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"""
        if "{{" not in text or "}}" not in text:
            raise ValueError(f"Invalid template format: {text}")

        parts = text.split("{{", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid template format: {text}")

        format_str = parts[0]
        var_part = parts[1].rstrip("}}").strip()

        if not var_part or not var_part.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid variable name: {var_part}")

        if var_part not in self.context:
            raise KeyError(f"Variable not found in context: {var_part}")

        date_value = self.context[var_part]
        if not hasattr(date_value, "strftime"):
            raise TypeError(f"Variable {var_part} is not a datetime object")

        return str(date_value.strftime(format_str))

    def truncate(self, text: str, render: Optional[Any] = None) -> str:
        """Truncate with ellipses: {{#truncate}}50{{description}}{{/truncate}}"""
        if "{{" not in text or "}}" not in text:
            raise ValueError(f"Invalid template format: {text}")

        parts = text.split("{{", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid template format: {text}")

        length_str = parts[0].strip()
        var_part = parts[1].rstrip("}}").strip()

        try:
            max_len = int(length_str)
        except ValueError:
            raise ValueError(f"Invalid length value: {length_str}")

        if max_len < 0:
            raise ValueError(f"Length must be non-negative: {max_len}")

        if not var_part or not var_part.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid variable name: {var_part}")

        if var_part not in self.context:
            raise KeyError(f"Variable not found in context: {var_part}")

        value = str(self.context[var_part])
        return value[:max_len] + "..." if len(value) > max_len else value

    def highlight_code(self, text: str, render: Optional[Any] = None) -> str:
        """Syntax highlight: {{#highlight_code}}python{{code_snippet}}{{/highlight_code}}"""
        if "{{" not in text or "}}" not in text:
            raise ValueError(f"Invalid template format: {text}")

        parts = text.split("{{", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid template format: {text}")

        language = parts[0].strip()
        var_part = parts[1].rstrip("}}").strip()

        if not language or not language.replace("-", "").replace("+", "").isalnum():
            raise ValueError(f"Invalid language name: {language}")

        if not var_part or not var_part.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid variable name: {var_part}")

        if var_part not in self.context:
            raise KeyError(f"Variable not found in context: {var_part}")

        code = str(self.context[var_part])
        return f"```{language}\n{code}\n```"
