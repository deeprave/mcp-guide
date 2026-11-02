"""Tests for template lambda functions."""

from collections import ChainMap
from datetime import datetime
from unittest.mock import patch

import pytest

from mcp_guide.core.tool_decorator import get_tool_prefix
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.functions import TemplateFunctions
from mcp_guide.render.recommendations import parse_recommendation
from mcp_guide.render.renderer import render_template_content


async def _identity(value: str) -> str:
    return value


class TestTemplateFunctions:
    """Test TemplateFunctions class."""

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


class TestCodeFence:
    """Tests for the language-labelled Markdown code-fence section."""

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
        context = TemplateContext({"invalid_date": "not_a_date"})

        result = await render_template_content("Date: {{#format_date}}%Y-{{invalid_date}}{{/format_date}}", context)

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        assert "[Template Error (" in rendered_content
        assert "not a datetime object" in rendered_content

    @pytest.mark.anyio
    async def test_safe_lambda_error_handling_truncate(self):
        """Test that safe lambda wrapper catches and formats errors for truncate."""
        # Negative length should trigger a validation error inside truncate
        context = TemplateContext({"text": "Some example content"})

        result = await render_template_content("{{#truncate}}-5{{text}}{{/truncate}}", context)

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        assert "[Template Error (" in rendered_content

    @pytest.mark.anyio
    async def test_safe_lambda_error_handling_highlight_code(self):
        """Test that safe lambda wrapper catches and formats errors for highlight_code."""
        # Invalid language name (contains invalid characters) should trigger a validation error
        context = TemplateContext({"code": "print('hello')"})

        result = await render_template_content("{{#highlight_code}}py@thon{{code}}{{/highlight_code}}", context)

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        assert "[Template Error (" in rendered_content


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

    @pytest.mark.anyio
    async def test_error_appends_message(self):
        fn = self._make()
        result = await fn._error("something went wrong", render=_identity)
        assert result == ""
        assert fn.errors == ["something went wrong"]

    @pytest.mark.anyio
    async def test_error_returns_empty_string(self):
        fn = self._make()
        assert await fn._error("msg", render=_identity) == ""

    @pytest.mark.anyio
    async def test_error_accumulates_multiple(self):
        fn = self._make()
        await fn._error("first", render=_identity)
        await fn._error("second", render=_identity)
        assert fn.errors == ["first", "second"]

    @pytest.mark.anyio
    async def test_error_empty_message_not_appended(self):
        fn = self._make()
        await fn._error("", render=_identity)
        assert fn.errors == []

    @pytest.mark.anyio
    async def test_error_uses_render_callable(self):
        fn = self._make({"name": "world"})

        async def render(_text: str) -> str:
            return "hello world"

        await fn._error("hello {{name}}", render=render)
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
        rendered_text = result.value.content
        errors = result.value.errors
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
        rendered_text = result.value.content
        assert rendered_text == "my-command"

    @pytest.mark.anyio
    async def test_no_error_gives_empty_list(self):
        """No _error invocation → empty errors list."""
        from mcp_guide.render.context import TemplateContext

        result = await render_template_content("hello", TemplateContext({}))
        assert result.success
        assert result.value is not None
        assert result.value.errors == []


class TestRecommendLambda:
    """Tests for embedded typed recommendations."""

    @pytest.mark.anyio
    async def test_recommend_renders_a_skill_reference_and_records_its_name(self):
        functions = TemplateFunctions(ChainMap())

        rendered = await functions.recommend("skill:workflow-review", render=_identity)

        recommendation = parse_recommendation("skill:workflow-review")
        assert rendered == f'Guide skill "workflow-review"[^{recommendation.label}]'
        assert functions.recommendations == [recommendation]

    @pytest.mark.anyio
    async def test_recommend_preserves_rendered_names_in_author_order(self):
        async def footnotes(_):
            return ""

        result = await render_template_content(
            "{{#recommend}}{{first}}{{/recommend}} {{#recommend}}{{second}}{{/recommend}}",
            TemplateContext({"first": "skill:workflow-status", "second": "content:docs"}),
            recommendation_footnotes=footnotes,
        )

        assert result.success
        assert result.value is not None
        skill = parse_recommendation("skill:workflow-status")
        content = parse_recommendation("content:docs")
        assert (
            result.value.content
            == f'Guide skill "workflow-status"[^{skill.label}] Guide content "docs"[^{content.label}]'
        )

    @pytest.mark.anyio
    async def test_recommend_preserves_repeated_rendered_names(self):
        async def footnotes(_):
            return ""

        result = await render_template_content(
            "{{#recommend}}workflow-review{{/recommend}} {{#recommend}}workflow-review{{/recommend}}",
            TemplateContext({}),
            recommendation_footnotes=footnotes,
        )

        assert result.success
        assert result.value is not None
        content = parse_recommendation("workflow-review")
        assert (
            result.value.content
            == f'Guide content "workflow-review"[^{content.label}] Guide content "workflow-review"[^{content.label}]'
        )
        assert result.value.content.count(content.label) == 2

    @pytest.mark.anyio
    async def test_empty_recommendation_is_an_error(self):
        functions = TemplateFunctions(ChainMap())

        with pytest.raises(ValueError, match="must name"):
            await functions.recommend("   ")
        assert functions.recommendations == []

    @pytest.mark.parametrize("value", ["unknown:target", ":target", "skill:"])
    @pytest.mark.anyio
    async def test_recommend_rejects_invalid_type_or_target(self, value):
        functions = TemplateFunctions(ChainMap())

        with pytest.raises(ValueError):
            await functions.recommend(value)


class TestResourceLambda:
    """Test resource template lambda."""

    @pytest.mark.parametrize(
        ("flags", "expression", "expected"),
        [
            ({}, "guidelines", "guide://guidelines"),
            ({"format-resource": False}, "guidelines", "guide://guidelines"),
            ({"format-resource": True}, "guidelines", 'get_content("guidelines")'),
            ({}, "guide,lang,context", "guide://guide,lang,context"),
            ({"format-resource": True}, "guide,lang,context", 'get_content("guide,lang,context")'),
            ({}, "  ", ""),
        ],
        ids=[
            "default_guide_uri",
            "flag_false_guide_uri",
            "flag_true_get_content",
            "comma_expression_guide_uri",
            "comma_expression_get_content",
            "empty_expression",
        ],
    )
    def test_resource_rendering_modes(self, flags: dict[str, bool], expression: str, expected: str):
        """resource should switch output mode based on the format-resource flag."""
        context = ChainMap({"flags": flags})
        functions = TemplateFunctions(context)

        result = functions.resource(expression)
        assert result == expected

    def test_flag_true_with_tool_prefix(self):
        """Flag true should prepend tool prefix to get_content() call."""
        context = ChainMap({"flags": {"format-resource": True}})
        functions = TemplateFunctions(context)

        get_tool_prefix.cache_clear()
        with patch.dict("os.environ", {"MCP_TOOL_PREFIX": "mcp_guide"}):
            result = functions.resource("guidelines")
        get_tool_prefix.cache_clear()
        assert result == 'mcp_guide_get_content("guidelines")'

    def test_no_flags_in_context(self):
        """Missing flags key should default to guide:// URI."""
        context = ChainMap({})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines")
        assert result == "guide://guidelines"

    def test_uses_raw_section_text(self):
        """The section callback preserves variable interpolation for Chevron."""
        context = ChainMap({"flags": {}})
        functions = TemplateFunctions(context)

        result = functions.resource("guidelines")
        assert result == "guide://guidelines"


class TestCommandLambda:
    """Test command template helper family."""

    @pytest.mark.anyio
    async def test_prompt_variable_uses_prompt_name_override(self):
        context = TemplateContext({})

        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "g"}):
            result = await render_template_content("{{prompt}}", context)

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        assert rendered_content == "g"

    @pytest.mark.anyio
    async def test_prompt_function_renders_its_result(self):
        """The explicit prompt function follows Chevron's interpolation protocol."""
        context = TemplateContext({"name": "Guide"})

        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "{{name}}"}):
            result = await render_template_content("{{prompt}}", context)

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == "Guide"

    @pytest.mark.anyio
    async def test_tool_prefix_variable_uses_prefix_override(self):
        """The explicit tool-prefix function resolves and escapes its configured prefix."""
        context = TemplateContext({})
        get_tool_prefix.cache_clear()
        try:
            with patch.dict("os.environ", {"MCP_TOOL_PREFIX": "<mcp>"}):
                result = await render_template_content("{{tool_prefix}}get_content", context)
        finally:
            get_tool_prefix.cache_clear()

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == "&lt;mcp&gt;_get_content"

    @pytest.mark.parametrize(
        ("configured_prefix", "expected"),
        [("", "None"), ("mcp", "mcp_")],
    )
    @pytest.mark.anyio
    async def test_tool_prefix_display_uses_status_fallback(self, monkeypatch, configured_prefix, expected):
        """The status-display function owns the blank-prefix fallback."""
        get_tool_prefix.cache_clear()
        try:
            monkeypatch.setenv("MCP_TOOL_PREFIX", configured_prefix)
            result = await render_template_content("{{tool_prefix_display}}", TemplateContext({}))
        finally:
            get_tool_prefix.cache_clear()

        assert result.is_ok()
        assert result.value is not None
        assert result.value.content == expected

    def test_command_defaults_to_uri(self):
        functions = TemplateFunctions(ChainMap({"flags": {}}))
        assert functions.command("status") == "guide://_status"

    @pytest.mark.anyio
    async def test_command_true_renders_prompt_style(self):
        functions = TemplateFunctions(ChainMap({"flags": {"format-command": True}, "@": "@"}))
        assert functions.command("status") == "@guide :status"
        assert await functions.command_args("now,later", _identity) == " now later"
        assert await functions.command_flags("verbose=true,force", _identity) == " --verbose=true --force"

    @pytest.mark.anyio
    async def test_command_false_renders_uri_fragments(self):
        functions = TemplateFunctions(ChainMap({"flags": {"format-command": False}}))
        assert functions.command("status") == "guide://_status"
        assert await functions.command_args("now,later", _identity) == "/now/later"
        assert await functions.command_flags("verbose=true,from=hello,force", _identity) == "?verbose&from=hello&force"

    @pytest.mark.anyio
    async def test_command_args_uri_encode_path_like_values(self):
        functions = TemplateFunctions(ChainMap({"flags": {"format-command": False}}))
        assert await functions.command_args("docs/,/external/data", _identity) == "/docs%2F/%2Fexternal%2Fdata"

    def test_command_uses_prompt_name_override(self):
        functions = TemplateFunctions(ChainMap({"flags": {"format-command": True}, "@": "/"}))
        with patch.dict("os.environ", {"MCP_PROMPT_NAME": "g"}):
            assert functions.command("status") == "/g :status"

    @pytest.mark.anyio
    async def test_command_alias_uses_selected_mode(self):
        uri_functions = TemplateFunctions(ChainMap({"flags": {}}))
        prompt_functions = TemplateFunctions(ChainMap({"flags": {"format-command": True}, "@": "@"}))

        assert (
            await uri_functions.command_alias("h,project/perm", _identity) == " (`guide://_h`, `guide://_project/perm`)"
        )
        assert (
            await prompt_functions.command_alias("h,project/perm", _identity)
            == " (`@guide :h`, `@guide :project/perm`)"
        )


class TestEqualsLambdas:
    """Test equals and notequals template lambdas."""

    @pytest.mark.parametrize(
        ("value", "expected_equals", "expected_notequals"),
        [
            ("same-issue", "MATCH", ""),
            ("other-issue", "", "DIFFERENT"),
        ],
        ids=["match", "mismatch"],
    )
    def test_literal_equals_and_notequals(self, value: str, expected_equals: str, expected_notequals: str):
        context = ChainMap({"workflow": {"issue": value}})
        functions = TemplateFunctions(context)

        assert functions.equals("same-issue{{workflow.issue}}MATCH") == expected_equals
        assert functions.notequals("same-issue{{workflow.issue}}DIFFERENT") == expected_notequals

    def test_notequals_renders_section_when_actual_value_is_missing(self):
        context = ChainMap({"workflow": {}})
        functions = TemplateFunctions(context)

        result = functions.notequals("same-issue{{workflow.issue}}DIFFERENT")
        assert result == "DIFFERENT"

    def test_equals_renders_section_when_two_variables_match(self):
        context = ChainMap(
            {
                "workflow": {"issue": "same-issue"},
                "args": [{"value": "same-issue", "first": True, "last": True}],
            }
        )
        functions = TemplateFunctions(context)

        result = functions.equals("{{args.0.value}}{{workflow.issue}}MATCH")
        assert result == "MATCH"

    def test_notequals_renders_section_when_two_variables_differ(self):
        context = ChainMap(
            {
                "workflow": {"issue": "other-issue"},
                "args": [{"value": "same-issue", "first": True, "last": True}],
            }
        )
        functions = TemplateFunctions(context)

        result = functions.notequals("{{args.0.value}}{{workflow.issue}}DIFFERENT")
        assert result == "DIFFERENT"


class TestWorkflowContainsLambdas:
    """Test workflow-scoped contains/notcontains lambdas."""

    @pytest.mark.anyio
    async def test_nested_workflow_contains_renders_body_for_configured_phase(self):
        context = TemplateContext(
            {
                "workflow": {
                    "phase_list": ["discussion", "planning", "implementation"],
                },
                "args": [{"value": "planning"}],
            }
        )

        result = await render_template_content(
            "{{#workflow.contains}}{{args.0.value}}OK: {{args.0.value}}{{/workflow.contains}}",
            context,
        )

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        errors = result.value.errors
        assert rendered_content == "OK: planning"
        assert errors == []

    @pytest.mark.anyio
    async def test_nested_workflow_contains_suppresses_body_for_missing_phase(self):
        context = TemplateContext(
            {
                "workflow": {
                    "phase_list": ["discussion", "implementation"],
                },
                "args": [{"value": "planning"}],
            }
        )

        result = await render_template_content(
            "{{#workflow.contains}}{{args.0.value}}OK: {{args.0.value}}{{/workflow.contains}}",
            context,
        )

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        errors = result.value.errors
        assert rendered_content == ""
        assert errors == []

    @pytest.mark.anyio
    async def test_nested_workflow_notcontains_renders_body_for_missing_phase(self):
        context = TemplateContext(
            {
                "workflow": {
                    "phase_list": ["discussion", "implementation"],
                },
                "args": [{"value": "planning"}],
            }
        )

        result = await render_template_content(
            "{{#workflow.notcontains}}{{args.0.value}}{{#_error}}Unknown or unavailable workflow phase: {{args.0.value}}{{/_error}}{{/workflow.notcontains}}",
            context,
        )

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        errors = result.value.errors
        assert rendered_content == ""
        assert errors == ["Unknown or unavailable workflow phase: planning"]

    @pytest.mark.anyio
    async def test_nested_workflow_notcontains_suppresses_body_for_configured_phase(self):
        context = TemplateContext(
            {
                "workflow": {
                    "phase_list": ["discussion", "planning", "implementation"],
                },
                "args": [{"value": "planning"}],
            }
        )

        result = await render_template_content(
            "{{#workflow.notcontains}}{{args.0.value}}NOPE{{/workflow.notcontains}}",
            context,
        )

        assert result.is_ok()
        assert result.value is not None
        rendered_content = result.value.content
        errors = result.value.errors
        assert rendered_content == ""
        assert errors == []
