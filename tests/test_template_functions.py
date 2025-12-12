"""Tests for template lambda functions."""

from collections import ChainMap
from datetime import datetime

import chevron
import pytest

from mcp_guide.utils.template_functions import SyntaxHighlighter, TemplateFunctions
from mcp_guide.utils.template_renderer import render_template_content


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
        context = ChainMap({"created_at": test_date})
        functions = TemplateFunctions(context)

        result = functions.format_date("%Y-%m-%d{{created_at}}")
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
        context = ChainMap({"created_at": datetime(2023, 12, 25)})
        functions = TemplateFunctions(context)

        with pytest.raises(ValueError, match="Invalid template format"):
            functions.format_date("no_braces")

        with pytest.raises(ValueError, match="Invalid template format"):
            functions.format_date("missing_close{{created_at")

    def test_format_date_invalid_variable_name(self):
        """Test format_date with invalid variable names."""
        context = ChainMap({"created_at": datetime(2023, 12, 25)})
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

    def test_safe_lambda_error_handling(self):
        """Test that safe lambda wrapper catches and formats errors."""
        context = ChainMap({"invalid_date": "not_a_date"})

        result = render_template_content("Date: {{#format_date}}%Y-{{invalid_date}}{{/format_date}}", context)

        assert result.is_ok()
        assert "[Template Error (" in result.value
        assert "not a datetime object" in result.value

    def test_safe_lambda_error_handling_truncate(self):
        """Test that safe lambda wrapper catches and formats errors for truncate."""
        # Negative length should trigger a validation error inside truncate
        context = ChainMap({"text": "Some example content"})

        result = render_template_content("{{#truncate}}-5{{text}}{{/truncate}}", context)

        assert result.is_ok()
        assert "[Template Error (" in result.value

    def test_safe_lambda_error_handling_highlight_code(self):
        """Test that safe lambda wrapper catches and formats errors for highlight_code."""
        # Invalid language name (contains invalid characters) should trigger a validation error
        context = ChainMap({"code": "print('hello')"})

        result = render_template_content("{{#highlight_code}}py@thon{{code}}{{/highlight_code}}", context)

        assert result.is_ok()
        assert "[Template Error (" in result.value

    def test_full_template_rendering_with_lambdas(self):
        """Test complete template rendering pipeline with lambda functions."""
        # Template with multiple lambda functions
        template = """# Project Report
Created: {{#format_date}}%B %d, %Y{{created_at}}{{/format_date}}
Description: {{#truncate}}50{{description}}{{/truncate}}

## Code Sample
{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}"""

        # Context with data and lambda functions
        base_context = ChainMap(
            {
                "created_at": datetime(2023, 12, 25, 14, 30, 0),
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
