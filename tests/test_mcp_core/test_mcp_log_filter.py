"""Tests for mcp_core.mcp_log_filter module."""


class TestRedactionStub:
    """Tests for PII redaction stub."""

    def test_redaction_function_passthrough(self):
        """Test redaction function returns input unchanged (pass-through)."""
        from mcp_guide.core.mcp_log_filter import get_redaction_function

        func = get_redaction_function()
        test_message = "sensitive data here"
        assert func(test_message) == test_message
