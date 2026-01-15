"""Agent data interception system with bit-flag registration."""

from enum import IntFlag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class EventType(IntFlag):
    """Bit-flag event types for efficient agent data routing."""

    FS_FILE_CONTENT = 1
    FS_DIRECTORY = 2
    FS_COMMAND = 4
    FS_CWD = 8
    TIMER = 65536  # 2^16
    TIMER_ONCE = 32768  # 2^15 - Timer that fires once then auto-unsubscribes


def is_timer_event(event_type: EventType) -> bool:
    """Check if event type includes timer bit."""
    return bool(event_type & (EventType.TIMER | EventType.TIMER_ONCE))
