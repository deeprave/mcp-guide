"""Agent data interception system with bit-flag registration."""

from dataclasses import dataclass
from enum import IntFlag
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .protocol import Task


class FSEventType(IntFlag):
    """Bit-flag filesystem event types for efficient agent data routing."""

    FILE_CONTENT = 1
    DIRECTORY_LISTING = 2
    COMMAND_LOCATION = 4
    WORKING_DIRECTORY = 8


@dataclass
class InterestRegistration:
    """Ephemeral interest registration for agent data."""

    task: "Task"
    flags: FSEventType
    callback: Callable[["FSEventType", dict[str, Any]], bool]
