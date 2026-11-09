"""Template lambda functions for Mustache templates."""

from collections import ChainMap
from datetime import datetime, timezone
from pathlib import Path
from shlex import quote as shell_quote
from typing import Any, Awaitable, Callable, cast
from urllib.parse import quote

import chevron

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import get_prompt_name
from mcp_guide.core.tool_decorator import get_tool_prefix
from mcp_guide.feature_flags.constants import FLAG_COMMAND, FLAG_RESOURCE
from mcp_guide.input_sources import workflow_phase_names
from mcp_guide.render.recommendations import Recommendation, parse_recommendation

logger = get_logger(__name__)
_MISSING = object()


class TemplateFunctions:
    """Template lambda functions with ChainMap context integration."""

    def __init__(self, context: ChainMap[str, Any], *, recommendations_enabled: bool = True) -> None:
        """Initialize with ChainMap context."""
        self.context = context
        self.errors: list[str] = []
        self.recommendations: list[Recommendation] = []
        self.recommendations_enabled = recommendations_enabled

    @chevron.compat
    async def _error(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Signal an application-level error: {{#_error}}message{{/_error}}"""
        try:
            message = await render(text) if render else text
        except Exception as e:
            logger.warning("_error lambda: render failed: %s", e)
            return ""
        if message:
            self.errors.append(message)
        return ""

    @chevron.compat
    async def recommend(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Render a typed Guide recommendation and retain its source for a footnote."""
        if not self.recommendations_enabled:
            raise RuntimeError("Recommendation rendering requires an active session")
        recommendation = parse_recommendation(await render(text) if render else text)
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
        return f'Guide {recommendation.kind} "{recommendation.name}"[^{recommendation.label}]'

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
        - indexed list access: `args.0.value`
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

    def _resolve_project_path(self, value: Any) -> str:
        """Resolve a configured client path against the shared project root."""
        candidate = Path(str(value))
        if candidate.is_absolute():
            return str(candidate)
        root = self._resolve_required_path("project.root")
        return str(Path(str(root)) / candidate)

    @chevron.func
    def documents_path(self) -> str:
        """Render the configured shared working-documents directory."""
        return self._resolve_project_path(self._resolve_required_path("path.documents"))

    @chevron.func
    def handoff_context_path(self) -> str:
        """Render the configured shared handoff-context file path."""
        return self._resolve_project_path(self._resolve_required_path("handoff_context.target"))

    def _parse_section_leading_var(self, text: str) -> tuple[str, str]:
        """Parse a section body that starts with a variable reference.

        Expected form:
            {{variable.path}}...body...
        """
        if not text.startswith("{{"):
            raise ValueError(f"Invalid template format: {text}")

        end = text.find("}}", 2)
        if end == -1:
            raise ValueError(f"Unterminated variable reference in template: {text}")

        var_part = text[2:end]
        body = text[end + 2 :]
        var_name = var_part.strip()
        self._validate_variable_name(var_name, text)
        return var_name, body

    def _get_workflow_phases(self) -> set[str]:
        """Return the configured workflow phases from context."""
        workflow = self._resolve_path("workflow")
        if workflow is _MISSING or not isinstance(workflow, dict):
            return set()

        return set(workflow_phase_names(workflow))

    @chevron.compat
    def format_date(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Format dates: {{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}"""
        format_str, var_name = self._parse_template_args(text)
        date_value = self._resolve_required_path(var_name)
        if not hasattr(date_value, "strftime"):
            raise TypeError(f"Variable {var_name} is not a datetime object")

        return str(date_value.strftime(format_str))

    @chevron.compat
    def truncate(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
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

    @chevron.compat
    async def shell_quote(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Shell-quote rendered command arguments."""
        return shell_quote(await render(text) if render else text)

    @chevron.compat
    def highlight_code(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Format a language-labelled Markdown code fence."""
        language, var_name = self._parse_template_args(text)

        if not language.strip() or not language.replace("-", "").replace("+", "").isalnum():
            raise ValueError(f"Invalid language name: {language}")

        code = str(self._resolve_required_path(var_name))
        return f"```{language}\n{code}\n```"

    @chevron.compat
    def pad_right(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Pad string to fixed width: {{#pad_right}}20{{command_name}}{{/pad_right}}"""
        try:
            width_str, var_name = self._parse_template_args(text)
            width = int(width_str.strip())

            value = str(self._resolve_required_path(var_name))
            return value.ljust(width)
        except ValueError as e:
            return f"[Pad Error: {e}]"

    @chevron.section
    def workflow_contains(self, text: str) -> str:
        """Check if a phase exists in configured workflow phases.

        Usage:
            {{#workflow.contains}}{{args.0.value}}...body...{{/workflow.contains}}
        """
        var_name, body = self._parse_section_leading_var(text)
        candidate = self._resolve_path(var_name)
        if candidate is _MISSING:
            return ""

        return body if str(candidate) in self._get_workflow_phases() else ""

    @chevron.section
    def workflow_notcontains(self, text: str) -> str:
        """Inverse of workflow_contains for phase membership checks."""
        var_name, body = self._parse_section_leading_var(text)
        candidate = self._resolve_path(var_name)
        if candidate is _MISSING:
            return ""

        return body if str(candidate) not in self._get_workflow_phases() else ""

    @chevron.compat
    def time_ago(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Format timestamp as relative time: {{#time_ago}}{{timestamp}}{{/time_ago}}"""
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

    def _comparison_section_body(self, text: str, *, negate: bool = False) -> str:
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

        return text[body_start:]

    @chevron.section
    def equals(self, text: str) -> str:
        """Compare values: {{#equals}}value{{variable}}{{/equals}}

        Returns the rendered section content if values match, empty string otherwise.
        """
        return self._comparison_section_body(text)

    @chevron.section
    def notequals(self, text: str) -> str:
        """Compare values: {{#notequals}}value{{variable}}{{/notequals}}

        Returns the rendered section content if values do not match, empty string otherwise.
        """
        return self._comparison_section_body(text, negate=True)

    @chevron.section
    def resource(self, text: str) -> str:
        """Render content reference: {{#resource}}expression{{/resource}}

        Returns guide://expression URI by default, or tool_prefix + get_content("expression")
        when the format-resource flag is true.
        """
        expression = text.strip()
        if not expression:
            return ""

        flags = self.context.get("flags", {})
        if flags.get(FLAG_RESOURCE):
            return f'{get_tool_prefix()}get_content("{expression}")'
        return f"guide://{expression}"

    def _get_prompt_reference_prefix(self) -> str:
        prompt_prefix = self.context.get("@", "")
        prompt_name = get_prompt_name()
        if prompt_prefix:
            return f"{prompt_prefix}{prompt_name} :"
        return f"{prompt_name} :"

    @staticmethod
    async def _parse_csv_items(text: str, render: Callable[[str], Awaitable[str]] | None = None) -> list[str]:
        value = (await render(text)).strip() if render else text.strip()
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @chevron.section
    def command(self, text: str) -> str:
        """Render command start: {{#command}}status{{/command}}."""
        command_name = text.strip()
        if not command_name:
            return ""
        flags = self.context.get("flags", {})
        if flags.get(FLAG_COMMAND):
            return f"{self._get_prompt_reference_prefix()}{command_name}"
        return f"guide://_{command_name}"

    @chevron.compat
    async def command_args(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Render command args fragment."""
        items = await self._parse_csv_items(text, render)
        if not items:
            return ""

        flags = self.context.get("flags", {})
        if flags.get(FLAG_COMMAND):
            return "".join(f" {item}" for item in items)
        return "".join(f"/{quote(item, safe='')}" for item in items)

    @chevron.compat
    async def command_flags(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Render command flags fragment."""
        items = await self._parse_csv_items(text, render)
        if not items:
            return ""

        flags = self.context.get("flags", {})
        if flags.get(FLAG_COMMAND):
            rendered_items: list[str] = []
            for item in items:
                if "=" in item:
                    name, value = item.split("=", 1)
                    rendered_items.append(f" --{name}={value}")
                else:
                    rendered_items.append(f" --{item}")
            return "".join(rendered_items)

        query_items: list[str] = []
        for item in items:
            if "=" in item:
                name, value = item.split("=", 1)
                if value.lower() == "true":
                    query_items.append(quote(name, safe=""))
                else:
                    query_items.append(f"{quote(name, safe='')}={quote(value, safe='')}")
            else:
                query_items.append(quote(item, safe=""))
        return f"?{'&'.join(query_items)}"

    @chevron.compat
    async def command_alias(self, text: str, render: Callable[[str], Awaitable[str]] | None = None) -> str:
        """Render aliases for a command reference."""
        items = await self._parse_csv_items(text, render)
        if not items:
            return ""

        flags = self.context.get("flags", {})
        if flags.get(FLAG_COMMAND):
            prefix = self._get_prompt_reference_prefix()
            return " (" + ", ".join(f"`{prefix}{item}`" for item in items) + ")"
        return " (" + ", ".join(f"`guide://_{item}`" for item in items) + ")"
