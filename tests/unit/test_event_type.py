"""Tests for EventType bitflag system."""

from mcp_guide.task_manager import EventType


def test_timer_event_identification():
    """Test timer event bit detection."""
    timer_event = EventType.TIMER | EventType.FS_FILE_CONTENT
    assert timer_event & EventType.TIMER

    # Test helper function
    from mcp_guide.task_manager.interception import is_timer_event

    assert is_timer_event(timer_event)
    assert is_timer_event(EventType.TIMER)
    assert not is_timer_event(EventType.FS_FILE_CONTENT)
