"""Template lambda functions for Mustache templates."""

from collections import ChainMap
from datetime import datetime, timezone
from typing import Any, Callable, cast

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_decorator import get_tool_prefix
from mcp_guide.feature_flags.constants import FLAG_CONTENT_ACCESSOR

logger = get_logger(__name__)
_MISSING = object()


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

        self._validate_variable_name(var_name, text)

        return arg_part, var_name

    @staticmethod
    def _validate_variable_name(var_name: str, text: str) -> None:
        """Validate a template variable/path name."""
        if not var_name:
            raise ValueError(f"Missing variable name in template: {text}")
        if var_name != "@" and not var_name.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError(f"Invalid variable name: {var_name}")

    def _resolve_path(self, var_name: str) -> Any:
        """Resolve a template variable/path against the existing context structure.

        Supports:
        - plain top-level names: `created_at`
        - dotted dict access: `workflow.issue`
        - indexed list access into IndexedList/list: `args.0.value`
        """
        self._validate_variable_name(var_name, var_name)

        if "." not in var_name:
            return self.context[var_name] if var_name in self.context else _MISSING

        parts = var_name.split(".")
        value: Any = self.context[parts[0]] if parts[0] in self.context else _MISSING
        for part in parts[1:]:
            if value is _MISSING:
                return _MISSING
            if isinstance(value, dict):
                value = cast(dict[str, Any], value).get(part, _MISSING)
                continue
            if isinstance(value, list):
                try:
                    value = value[int(part)]
                except (ValueError, IndexError):
                    return _MISSING
                continue
            return _MISSING
        return value

    def _resolve_required_path(self, var_name: str) -> Any:
        """Resolve a required variable/path or raise KeyError."""
        value = self._resolve_path(var_name)
        if value is _MISSING:
            raise KeyError(f"Variable not found in context: {var_name}")
        return value

    def format_date(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Format dates: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"""
        format_str, var_name = self._parse_template_args(text)
        date_value = self._resolve_required_path(var_name)
        if not hasattr(date_value, "strftime"):
            raise TypeError(f"Variable {var_name} is not a datetime object")

        return str(date_value.strftime(format_str))

    def truncate(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Truncate with ellipses: {{#truncate}}50{{description}}{{/truncate}}"""
        length_str, var_name = self._parse_template_args(text)

        try:
            max_len = int(length_str.strip())
        except ValueError:
            raise ValueError(f"Invalid length value: {length_str}")

        if max_len < 0:
            raise ValueError(f"Length must be non-negative: {max_len}")

        value = str(self._resolve_required_path(var_name))
        return value[:max_len] + "..." if len(value) > max_len else value

    def highlight_code(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Syntax highlight: {{#highlight_code}}python{{code_snippet}}{{/highlight_code}}"""
        language, var_name = self._parse_template_args(text)

        if not language.strip() or not language.replace("-", "").replace("+", "").isalnum():
            raise ValueError(f"Invalid language name: {language}")

        code = str(self._resolve_required_path(var_name))
        return f"```{language}\n{code}\n```"

    def pad_right(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Pad string to fixed width: {{#pad_right}}20{{command_name}}{{/pad_right}}"""
        try:
            width_str, var_name = self._parse_template_args(text)
            width = int(width_str.strip())

            value = str(self._resolve_required_path(var_name))
            return value.ljust(width)
        except ValueError as e:
            return f"[Pad Error: {e}]"

    def contains(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Check if value contains substring: {{#contains}}substring{{variable}}{{/contains}}"""
        substring, var_name = self._parse_template_args(text)

        actual_value = self._resolve_path(var_name)
        if actual_value is _MISSING:
            return ""

        actual = str(actual_value)
        return render(text) if render and substring.strip() in actual else ""

    def time_ago(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Format timestamp as relative time: {{#time_ago}}{{exported_at}}{{/time_ago}}"""
        _, var_name = self._parse_template_args(text)

        value = self._resolve_path(var_name)
        if value is _MISSING:
            return ""
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

    def _parse_comparison_args(self, text: str) -> tuple[str | None, str, int]:
        """Parse equals/notequals lambda args.

        Supported forms:
            literal{{variable}}...
            {{expected_var}}{{actual_var}}...

        Returns:
            Tuple of (expected_literal or expected_var_name, actual_var_name, body_start_index)
            If text starts with a variable reference, expected_literal contains the first variable name.
        """
        if text.startswith("{{"):
            if "}}" not in text:
                raise ValueError(f"Invalid template format: {text}")

            first_var, remainder = text[2:].split("}}", 1)
            first_var = first_var.strip()
            self._validate_variable_name(first_var, text)

            if not remainder.startswith("{{") or "}}" not in remainder:
                raise ValueError(f"Invalid template format: {text}")

            second_var, _ = remainder[2:].split("}}", 1)
            second_var = second_var.strip()
            self._validate_variable_name(second_var, text)

            second_end = text.find("}}", text.find("}}") + 2) + 2
            return first_var, second_var, second_end

        expected, var_name = self._parse_template_args(text)
        body_start = text.find("}}") + 2
        return expected.strip(), var_name, body_start

    def _render_comparison(self, text: str, render: Callable[[str], str] | None, *, negate: bool = False) -> str:
        expected_or_var, var_name, body_start = self._parse_comparison_args(text)
        actual_value = self._resolve_path(var_name)

        if text.startswith("{{"):
            expected_value = self._resolve_path(expected_or_var or "")
            expected = str(expected_value) if expected_value is not _MISSING else None
        else:
            expected = expected_or_var or ""

        actual = str(actual_value) if actual_value is not _MISSING else None
        matches = (actual is not None) and (expected is not None) and actual == expected
        if negate:
            matches = not matches
        if not matches:
            return ""

        if render:
            return str(render(text[body_start:]))
        return ""

    def equals(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Compare values: {{#equals}}value{{variable}}{{/equals}}

        Returns the rendered section content if values match, empty string otherwise.
        """
        return self._render_comparison(text, render)

    def notequals(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Compare values: {{#notequals}}value{{variable}}{{/notequals}}

        Returns the rendered section content if values do not match, empty string otherwise.
        """
        return self._render_comparison(text, render, negate=True)

    def resource(self, text: str, render: Callable[[str], str] | None = None) -> str:
        """Render content reference: {{#resource}}expression{{/resource}}

        Returns guide://expression URI by default, or tool_prefix + get_content("expression")
        when the content-accessor flag is true.
        """
        expression = render(text).strip() if render else text.strip()
        if not expression:
            return ""

        flags = self.context.get("flags", {})
        if flags.get(FLAG_CONTENT_ACCESSOR):
            return f'{get_tool_prefix()}get_content("{expression}")'
        return f"guide://{expression}"
