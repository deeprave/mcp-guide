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

    def equals(self, text: str, render: Optional[Any] = None) -> str:
        """Compare values: {{#equals}}value{{variable}}{{/equals}}"""
        expected, var_name = self._parse_template_args(text)

        if var_name not in self.context:
            return ""

        actual = str(self.context[var_name])
        return render(text) if render and actual == expected.strip() else ""

    def contains(self, text: str, render: Optional[Any] = None) -> str:
        """Check if value contains substring: {{#contains}}substring{{variable}}{{/contains}}"""
        substring, var_name = self._parse_template_args(text)

        if var_name not in self.context:
            return ""

        actual = str(self.context[var_name])
        return render(text) if render and substring.strip() in actual else ""
