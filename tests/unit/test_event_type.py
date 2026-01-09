"""Tests for EventType bitflag system."""

from mcp_guide.task_manager import EventType


def test_event_type_enum_values():
    """Test EventType has all required values."""
    assert EventType.FS_FILE_CONTENT == 1
    assert EventType.FS_DIRECTORY == 2
    assert EventType.FS_COMMAND == 4
    assert EventType.FS_CWD == 8
    assert EventType.TIMER == 65536


def test_event_type_bitwise_operations():
    """Test bitwise OR and AND operations."""
    combined = EventType.FS_FILE_CONTENT | EventType.TIMER
    assert combined & EventType.FS_FILE_CONTENT
    assert combined & EventType.TIMER
    assert not (combined & EventType.FS_DIRECTORY)


def test_timer_event_identification():
    """Test timer event bit detection."""
    timer_event = EventType.TIMER | EventType.FS_FILE_CONTENT
    assert timer_event & EventType.TIMER

    # Test helper function
    from mcp_guide.task_manager.interception import is_timer_event

    assert is_timer_event(timer_event)
    assert is_timer_event(EventType.TIMER)
    assert not is_timer_event(EventType.FS_FILE_CONTENT)


def test_event_type_combinations():
    """Test various EventType combinations."""
    # Multiple non-timer events
    multi = EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY
    assert multi & EventType.FS_FILE_CONTENT
    assert multi & EventType.FS_DIRECTORY
    assert not (multi & EventType.TIMER)

    # Timer with multiple other events
    timer_multi = EventType.TIMER | EventType.FS_FILE_CONTENT | EventType.FS_COMMAND
    assert timer_multi & EventType.TIMER
    assert timer_multi & EventType.FS_FILE_CONTENT
    assert timer_multi & EventType.FS_COMMAND
    assert not (timer_multi & EventType.FS_DIRECTORY)
