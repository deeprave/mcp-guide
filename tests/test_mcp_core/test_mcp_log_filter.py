"""Tests for mcp_core.mcp_log_filter module."""


class TestRedactionStub:
    """Tests for PII redaction stub."""

    def test_get_redaction_function_returns_callable(self):
        """Test get_redaction_function returns a callable."""
        from mcp_guide.core.mcp_log_filter import get_redaction_function

        func = get_redaction_function()
        assert callable(func)

    def test_redaction_function_accepts_string(self):
        """Test redaction function accepts string argument."""
        from mcp_guide.core.mcp_log_filter import get_redaction_function

        func = get_redaction_function()
        result = func("test message")
        assert isinstance(result, str)

    def test_redaction_function_passthrough(self):
        """Test redaction function returns input unchanged (pass-through)."""
        from mcp_guide.core.mcp_log_filter import get_redaction_function

        func = get_redaction_function()
        test_message = "sensitive data here"
        assert func(test_message) == test_message
