"""Named source-template cases for Guide's public rendering boundary."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mcp_guide.render.context import TemplateContext


@dataclass(frozen=True)
class TemplateRenderCase:
    """One ordinary source-template rendering scenario."""

    name: str
    template: str
    expected: str
    context: Mapping[str, Any] = field(default_factory=dict)
    partials: Mapping[str, str] = field(default_factory=dict)
    file_path: str = "<template>"

    def render_context(self) -> TemplateContext:
        """Create the data-only context for this independent render."""
        return TemplateContext(dict(self.context))


TEMPLATE_RENDER_CASES = (
    TemplateRenderCase(
        name="interpolates a variable",
        template="Hello {{name}}",
        context={"name": "Guide"},
        expected="Hello Guide",
    ),
    TemplateRenderCase(
        name="resolves dotted context",
        template="Hello {{name}}! Project: {{project.name}}",
        context={"name": "World", "project": {"name": "test-project"}},
        expected="Hello World! Project: test-project",
    ),
    TemplateRenderCase(
        name="expands a section",
        template="{{#items}}[{{name}}]{{/items}}",
        context={"items": [{"name": "one"}, {"name": "two"}]},
        expected="[one][two]",
    ),
    TemplateRenderCase(
        name="expands an inverted section",
        template="{{^items}}empty{{/items}}",
        context={"items": []},
        expected="empty",
    ),
    TemplateRenderCase(
        name="uses changed delimiters",
        template="{{=<% %>=}}<%name%>",
        context={"name": "Guide"},
        expected="Guide",
    ),
    TemplateRenderCase(
        name="renders a missing value as empty",
        template="Hello {{missing_var}}!",
        expected="Hello !",
    ),
    TemplateRenderCase(
        name="renders an in-memory partial",
        template="{{>project}}",
        context={"project_name": "test-project"},
        partials={"project": "Project: {{project_name}}"},
        expected="Project: test-project",
    ),
    TemplateRenderCase(
        name="awaits a registered extension in an in-memory partial",
        template="{{>command}}",
        context={"flags": {}, "values": "one,two"},
        partials={"command": "Use {{#command-args}}{{values}}{{/command-args}}."},
        expected="Use /one/two.",
    ),
    TemplateRenderCase(
        name="ignores a missing in-memory partial",
        template="{{>missing}}",
        expected="",
    ),
    TemplateRenderCase(
        name="formats a date through the registered section extension",
        template="Date: {{#format_date}}%Y-%m-%d{{event_date}}{{/format_date}}",
        context={"event_date": datetime(2023, 12, 25)},
        expected="Date: 2023-12-25",
    ),
    TemplateRenderCase(
        name="truncates text through the registered section extension",
        template="Text: {{#truncate}}10{{long_text}}{{/truncate}}",
        context={"long_text": "This is a very long text that should be truncated"},
        expected="Text: This is a ...",
    ),
    TemplateRenderCase(
        name="formats a Markdown code fence through the registered section extension",
        template="Code: {{#highlight_code}}python{{code}}{{/highlight_code}}",
        context={"code": "print('hello')"},
        expected="Code: ```python\nprint('hello')\n```",
    ),
    TemplateRenderCase(
        name="preserves Mustache syntax in highlighted code",
        template="{{#highlight_code}}python{{code}}{{/highlight_code}}",
        context={
            "name": "expanded",
            "code": "print('{{name}}')\n{{! source comment}}\n{{#_error}}not an error{{/_error}}\n{{open",
        },
        expected="```python\nprint('{{name}}')\n{{! source comment}}\n{{#_error}}not an error{{/_error}}\n{{open\n```",
    ),
    TemplateRenderCase(
        name="truncates original text before inserting it",
        template="{{#truncate}}12{{value}}{{/truncate}}",
        context={"name": "expanded", "value": "{{name}} world"},
        expected="{{name}} wor...",
    ),
    TemplateRenderCase(
        name="pads literal output without expanding it",
        template="{{#pad_right}}16{{value}}{{/pad_right}}",
        context={"secret": "expanded", "value": "x {{secret}}"},
        expected="x {{secret}}    ",
    ),
    TemplateRenderCase(
        name="renders an interpolated resource expression",
        template="Read {{#resource}}{{category}}/{{name}}{{/resource}}.",
        context={"category": "docs", "name": "tracking"},
        expected="Read guide://docs/tracking.",
    ),
    TemplateRenderCase(
        name="renders a command with interpolated name",
        template="Use {{#command}}{{name}}{{/command}}.",
        context={"flags": {}, "name": "workflow/status"},
        expected="Use guide://_workflow/status.",
    ),
    TemplateRenderCase(
        name="renders a command with interpolated name in prompt mode",
        template="Use {{#command}}{{name}}{{/command}}.",
        context={"flags": {"format-command": True}, "@": "/", "name": "workflow/status"},
        expected="Use /guide :workflow/status.",
    ),
    TemplateRenderCase(
        name="renders command arguments from interpolated CSV",
        template="{{#command-args}}{{values}}{{/command-args}}",
        context={"flags": {}, "values": "one,two"},
        expected="/one/two",
    ),
    TemplateRenderCase(
        name="renders command flags from interpolated CSV",
        template="{{#command-flags}}{{values}}{{/command-flags}}",
        context={"flags": {}, "values": "verbose=true,force"},
        expected="?verbose&force",
    ),
    TemplateRenderCase(
        name="renders command aliases from interpolated CSV",
        template="{{#command-alias}}{{values}}{{/command-alias}}",
        context={"flags": {}, "values": "help,status"},
        expected=" (`guide://_help`, `guide://_status`)",
    ),
    TemplateRenderCase(
        name="renders command aliases alongside a command",
        template="- `{{#command}}help{{/command}}`{{#aliases_csv}}{{#command-alias}}{{.}}{{/command-alias}}{{/aliases_csv}}",
        context={"flags": {}, "aliases_csv": "h,project/perm"},
        expected="- `guide://_help` (`guide://_h`, `guide://_project/perm`)",
    ),
    TemplateRenderCase(
        name="renders a selected conditional section body",
        template="{{#equals}}same{{value}}Matches {{value}}{{/equals}}",
        context={"value": "same"},
        expected="Matches same",
    ),
    TemplateRenderCase(
        name="renders an inverse conditional section body",
        template="{{#notequals}}same{{value}}Differs {{value}}{{/notequals}}",
        context={"value": "other"},
        expected="Differs other",
    ),
)
