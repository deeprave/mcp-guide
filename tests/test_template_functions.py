"""Tests for template lambda functions."""

from collections import ChainMap
from datetime import datetime
from unittest.mock import patch

import chevron
import pytest

from mcp_guide.core.tool_decorator import get_tool_prefix
from mcp_guide.render.functions import SyntaxHighlighter, TemplateFunctions
from mcp_guide.render.renderer import render_template_content


class TestTemplateFunctions:
    """Test TemplateFunctions class."""

    def test_init_with_chainmap_context(self):
        """Test TemplateFunctions initialization with ChainMap context."""
        context = ChainMap({"key": "value"})
        functions = TemplateFunctions(context)

        assert functions.context is context
        assert functions.context["key"] == "value"

    def test_format_date_lambda(self):
        """Test format_date lambda function."""
        test_date = datetime(2023, 12, 25, 14, 30, 0)
        context = ChainMap({"event_date": test_date})
        functions = TemplateFunctions(context)

        result = functions.format_date("%Y-%m-%d{{event_date}}")
        assert result == "2023-12-25"

    def test_truncate_lambda(self):
        """Test truncate lambda function."""
        context = ChainMap({"description": "This is a very long description that should be truncated"})
        functions = TemplateFunctions(context)

        result = functions.truncate("20{{description}}")
        assert result == "This is a very long ..."


class TestSyntaxHighlighter:
    """Test SyntaxHighlighter class."""

    def test_init_checks_pygments(self):
        """Test SyntaxHighlighter initialization checks for Pygments."""
        highlighter = SyntaxHighlighter()

        assert hasattr(highlighter, "pygments_available")
        assert isinstance(highlighter.pygments_available, bool)

    def test_highlight_code_lambda(self):
        """Test highlight_code lambda function."""
        context = ChainMap({"code_snippet": 'def hello():\n    print("Hello")'})
        functions = TemplateFunctions(context)

        result = functions.highlight_code("python{{code_snippet}}")
        assert result.startswith("```python\n")
        assert result.endswith("\n```")
        assert "def hello():" in result


class TestTemplateFunctionsSecurity:
    """Test security validations in template functions."""

    def test_format_date_invalid_template_format(self):
        """Test format_date with invalid template format."""
        context = ChainMap({"event_date": datetime(2023, 12, 25)})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Invalid template format"):
            functions.format_date("no_braces")

        with pytest.raises(ValueError, match="Invalid template format"):
            functions.format_date("missing_close{{event_date")

    def test_format_date_invalid_variable_name(self):
        """Test format_date with invalid variable names."""
        context = ChainMap({"event_date": datetime(2023, 12, 25)})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Missing variable name"):
            functions.format_date("%Y-{{}}")  # Empty variable

        with pytest.raises(ValueError, match="Invalid variable name"):
            functions.format_date("%Y-{{invalid@var}}")  # Invalid characters

    def test_format_date_missing_variable(self):
        """Test format_date with missing context variable."""
        context = ChainMap({"other_var": datetime(2023, 12, 25)})
        functions = TemplateFunctions(context)

        with pytest.raises(KeyError, match="Variable not found in context"):
            functions.format_date("%Y-{{missing_var}}")

    def test_format_date_wrong_type(self):
        """Test format_date with non-datetime variable."""
        context = ChainMap({"not_date": "string_value"})
        functions = TemplateFunctions(context)

        with pytest.raises(TypeError, match="not a datetime object"):
            functions.format_date("%Y-{{not_date}}")

    def test_truncate_invalid_length(self):
        """Test truncate with invalid length values."""
        context = ChainMap({"description": "test text"})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Invalid length value"):
            functions.truncate("abc{{description}}")

        with pytest.raises(ValueError, match="Length must be non-negative"):
            functions.truncate("-5{{description}}")

    def test_truncate_invalid_variable_name(self):
        """Test truncate with an invalid variable name."""
        context = ChainMap({"description": "test text"})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Invalid variable name"):
            functions.truncate("10{{invalid@var}}")

    def test_truncate_missing_variable(self):
        """Test truncate with a missing context variable."""
        context = ChainMap({"description": "test text"})
        functions = TemplateFunctions(context)

        with pytest.raises(KeyError, match="missing_var"):
            functions.truncate("10{{missing_var}}")

    def test_highlight_code_invalid_language(self):
        """Test highlight_code with invalid language names."""
        context = ChainMap({"code": 'print("hello")'})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Invalid language name"):
            functions.highlight_code("{{code}}")  # Empty language

        with pytest.raises(ValueError, match="Invalid language name"):
            functions.highlight_code("py@thon{{code}}")  # Invalid characters

    def test_highlight_code_invalid_template_syntax(self):
        """Test highlight_code with invalid template syntax."""
        context = ChainMap({"code": 'print("hello")'})
        functions = TemplateFunctions(context)

        # Missing closing braces for the variable placeholder
        with pytest.raises(ValueError, match="Invalid template"):
            functions.highlight_code("python{{code")

    def test_highlight_code_invalid_variable_name(self):
        """Test highlight_code with invalid variable names."""
        context = ChainMap({"code": 'print("hello")'})
        functions = TemplateFunctions(context)

        # Variable name contains invalid characters
        with pytest.raises(ValueError, match="Invalid variable name"):
            functions.highlight_code("python{{invalid@var}}")

    def test_highlight_code_missing_variable_in_context(self):
        """Test highlight_code with missing variables in the context."""
        context = ChainMap({})
        functions = TemplateFunctions(context)

        # Referencing a variable that is not present in the context
        with pytest.raises(KeyError):
            functions.highlight_code("python{{missing_var}}")


class TestSafeLambdaWrapper:
    """Test safe lambda wrapper functionality."""

    @pytest.mark.anyio
    async def test_safe_lambda_error_handling(self):
        """Test that safe lambda wrapper catches and formats errors."""
        context = ChainMap({"invalid_date": "not_a_date"})

        result = await render_template_content("Date: {{#format_date}}%Y-{{invalid_date}}{{/format_date}}", context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert "[Template Error (" in rendered_content
        assert "not a datetime object" in rendered_content

    @pytest.mark.anyio
    async def test_safe_lambda_error_handling_truncate(self):
        """Test that safe lambda wrapper catches and formats errors for truncate."""
        # Negative length should trigger a validation error inside truncate
        context = ChainMap({"text": "Some example content"})

        result = await render_template_content("{{#truncate}}-5{{text}}{{/truncate}}", context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert "[Template Error (" in rendered_content

    @pytest.mark.anyio
    async def test_safe_lambda_error_handling_highlight_code(self):
        """Test that safe lambda wrapper catches and formats errors for highlight_code."""
        # Invalid language name (contains invalid characters) should trigger a validation error
        context = ChainMap({"code": "print('hello')"})

        result = await render_template_content("{{#highlight_code}}py@thon{{code}}{{/highlight_code}}", context)

        assert result.is_ok()
        rendered_content, _, _ = result.value
        assert "[Template Error (" in rendered_content

    def test_full_template_rendering_with_lambdas(self):
        """Test complete template rendering pipeline with lambda functions."""
        # Template with multiple lambda functions
        template = """# Project Report
Created: {{#format_date}}%B %d, %Y{{event_date}}{{/format_date}}
Description: {{#truncate}}50{{description}}{{/truncate}}

## Code Sample
{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}"""

        # Context with data and lambda functions
        base_context = ChainMap(
            {
                "event_date": datetime(2023, 12, 25, 14, 30, 0),
                "description": "This is a very long project description that should be truncated for display",
                "code_snippet": 'def main():\n    print("Hello World")',
            }
        )

        functions = TemplateFunctions(base_context)
        context = base_context.new_child(
            {
                "format_date": functions.format_date,
                "truncate": functions.truncate,
                "highlight_code": functions.highlight_code,
            }
        )

        result = chevron.render(template, context)

        assert "December 25, 2023" in result
        assert "This is a very long project description that shoul..." in result
        assert "```python\ndef main():" in result


class TestTimeAgoLambda:
    """Tests for time_ago lambda function."""

    def _make(self, value):
        return TemplateFunctions(ChainMap({"ts": value}))

    @pytest.mark.parametrize(
        "value",
        [None, 0, 0.0],
        ids=["none", "zero_int", "zero_float"],
    )
    def test_time_ago_falsy_returns_unknown(self, value):
        result = self._make(value).time_ago("{{ts}}")
        assert result == "unknown"

    def test_time_ago_minutes(self):
        import time

        ts = time.time() - 90  # 1m30s ago
        result = self._make(ts).time_ago("{{ts}}")
        assert result == "1m ago"

    def test_time_ago_hours(self):
        import time

        ts = time.time() - 3700  # ~1h1m ago
        result = self._make(ts).time_ago("{{ts}}")
        assert result == "1h1m ago"

    def test_time_ago_days(self):
        import time

        ts = time.time() - 86400 * 2 - 3600  # 2d1h ago
        result = self._make(ts).time_ago("{{ts}}")
        assert result == "2d1h ago"

    def test_time_ago_invalid_type_raises(self):
        with pytest.raises(TypeError):
            self._make("not-a-timestamp").time_ago("{{ts}}")


class TestErrorLambda:
    """Tests for the _error template lambda."""

    def _make(self, extra: dict | None = None) -> TemplateFunctions:
        return TemplateFunctions(ChainMap(extra or {}))

    def test_error_appends_message(self):
        fn = self._make()
        result = fn._error("something went wrong", render=lambda t: t)
        assert result == ""
        assert fn.errors == ["something went wrong"]

    def test_error_returns_empty_string(self):
        fn = self._make()
        assert fn._error("msg", render=lambda t: t) == ""

    def test_error_accumulates_multiple(self):
        fn = self._make()
        fn._error("first", render=lambda t: t)
        fn._error("second", render=lambda t: t)
        assert fn.errors == ["first", "second"]

    def test_error_empty_message_not_appended(self):
        fn = self._make()
        fn._error("", render=lambda t: t)
        assert fn.errors == []

    def test_error_uses_render_callable(self):
        fn = self._make({"name": "world"})
        fn._error("hello {{name}}", render=lambda t: "hello world")
        assert fn.errors == ["hello world"]

    @pytest.mark.anyio
    async def test_error_propagates_via_rendered_content(self):
        """_error in template body propagates to RenderedContent.errors."""
        from mcp_guide.render.context import TemplateContext

        template = "{{#_error}}missing arg{{/_error}}"
        ctx = TemplateContext({})
        result = await render_template_content(template, ctx)
        assert result.success
        assert result.value is not None
        rendered_text, _, errors = result.value
        assert rendered_text == ""
        assert errors == ["missing arg"]

    @pytest.mark.anyio
    async def test_template_name_injected(self):
        """template_name is injected as the stem of file_path."""
        from mcp_guide.render.context import TemplateContext

        template = "{{template_name}}"
        ctx = TemplateContext({})
        result = await render_template_content(template, ctx, file_path="path/to/_my-command.mustache")
        assert result.success
        assert result.value is not None
        rendered_text, _, _ = result.value
        assert rendered_text == "my-command"

    @pytest.mark.anyio
    async def test_no_error_gives_empty_list(self):
        """No _error invocation → empty errors list."""
        from mcp_guide.render.context import TemplateContext

        result = await render_template_content("hello", TemplateContext({}))
        assert result.success
        assert result.value is not None
        _, _, errors = result.value
        assert errors == []


class TestResourceLambda:
    """Test resource template lambda."""

    def test_default_renders_guide_uri(self):
        """Default (no flag) should render as guide:// URI."""
        context = ChainMap({"flags": {}})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines", lambda t: t)
        assert result == "guide://guidelines"

    def test_flag_false_renders_guide_uri(self):
        """Explicit false flag should render as guide:// URI."""
        context = ChainMap({"flags": {"content-accessor": False}})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines", lambda t: t)
        assert result == "guide://guidelines"

    def test_flag_true_renders_get_content(self):
        """Flag true should render as get_content() call."""
        context = ChainMap({"flags": {"content-accessor": True}})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines", lambda t: t)
        assert result == 'get_content("guidelines")'

    def test_flag_true_with_tool_prefix(self):
        """Flag true should prepend tool prefix to get_content() call."""
        context = ChainMap({"flags": {"content-accessor": True}})
        functions = TemplateFunctions(context)

        get_tool_prefix.cache_clear()
        with patch.dict("os.environ", {"MCP_TOOL_PREFIX": "mcp_guide"}):
            result = functions.resource("guidelines", lambda t: t)
        get_tool_prefix.cache_clear()
        assert result == 'mcp_guide_get_content("guidelines")'

    def test_comma_expression_with_flag_false(self):
        """Comma expressions should render as guide:// URI when flag is false."""
        context = ChainMap({"flags": {}})
        functions = TemplateFunctions(context)

        result = functions.resource("guide,lang,context", lambda t: t)
        assert result == "guide://guide,lang,context"

    def test_comma_expression_with_flag_true(self):
        """Comma expressions should render as get_content() when flag is true."""
        context = ChainMap({"flags": {"content-accessor": True}})
        functions = TemplateFunctions(context)

        result = functions.resource("guide,lang,context", lambda t: t)
        assert result == 'get_content("guide,lang,context")'

    def test_empty_expression_returns_empty(self):
        """Empty expression should return empty string."""
        context = ChainMap({"flags": {}})
        functions = TemplateFunctions(context)

        result = functions.resource("  ", lambda t: t)
        assert result == ""

    def test_no_flags_in_context(self):
        """Missing flags key should default to guide:// URI."""
        context = ChainMap({})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines", lambda t: t)
        assert result == "guide://guidelines"

    def test_render_none_uses_raw_text(self):
        """When render is None, should use raw text directly."""
        context = ChainMap({"flags": {}})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines")
        assert result == "guide://guidelines"


class TestEqualsLambdas:
    """Test equals and notequals template lambdas."""

    def test_equals_renders_section_when_values_match(self):
        context = ChainMap({"workflow": {"issue": "same-issue"}})
        functions = TemplateFunctions(context)

        result = functions.equals("same-issue{{workflow.issue}}MATCH", lambda t: t)
        assert result == "MATCH"

    def test_equals_returns_empty_when_values_do_not_match(self):
        context = ChainMap({"workflow": {"issue": "other-issue"}})
        functions = TemplateFunctions(context)

        result = functions.equals("same-issue{{workflow.issue}}MATCH", lambda t: t)
        assert result == ""

    def test_notequals_renders_section_when_values_do_not_match(self):
        context = ChainMap({"workflow": {"issue": "other-issue"}})
        functions = TemplateFunctions(context)

        result = functions.notequals("same-issue{{workflow.issue}}DIFFERENT", lambda t: t)
        assert result == "DIFFERENT"

    def test_notequals_returns_empty_when_values_match(self):
        context = ChainMap({"workflow": {"issue": "same-issue"}})
        functions = TemplateFunctions(context)

        result = functions.notequals("same-issue{{workflow.issue}}DIFFERENT", lambda t: t)
        assert result == ""
