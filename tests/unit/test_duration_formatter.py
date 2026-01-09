"""Tests for duration formatting utilities."""

from mcp_guide.utils.duration_formatter import format_duration


class TestDurationFormatter:
    """Test duration formatting functionality."""

    def test_format_duration_seconds_only(self):
        """Test formatting durations under 1 minute."""
        assert format_duration(27.5) == "27.5s"
        assert format_duration(45.0) == "45.0s"
        assert format_duration(0.1) == "0.1s"

    def test_format_duration_minutes_and_seconds(self):
        """Test formatting durations with minutes."""
        assert format_duration(272.51) == "4m32.5s"
        assert format_duration(90.0) == "1m30.0s"
        assert format_duration(120.5) == "2m0.5s"

    def test_format_duration_hours_minutes_seconds(self):
        """Test formatting durations with hours."""
        assert format_duration(28228.91) == "7h50m28.9s"
        assert format_duration(3661.2) == "1h1m1.2s"
        assert format_duration(7200.0) == "2h0m0.0s"

    def test_format_duration_edge_cases(self):
        """Test edge cases for duration formatting."""
        assert format_duration(0) == "0.0s"
        assert format_duration(60) == "1m0.0s"
        assert format_duration(3600) == "1h0m0.0s"
        assert format_duration(3660) == "1h1m0.0s"
