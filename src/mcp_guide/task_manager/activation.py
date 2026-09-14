"""Explicit lifecycle authority for one project-scoped task."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from .interception import EventType

if TYPE_CHECKING:
    from mcp_guide.session import Session

    from .manager import TaskManager
    from .protocol import TaskSubscriber


class TaskActivation:
    """Own the mutable TaskManager state produced by one project task.

    A project task receives this capability during startup and retains it for
    its callbacks. Retirement is idempotent and makes later state writes safe
    no-ops, including writes from callbacks that resume after replacement.
    """

    def __init__(self, manager: "TaskManager", task: "TaskSubscriber", session: "Session") -> None:
        self._manager = manager
        self._task = task
        self._session = session
        self._retired = False

    @property
    def session(self) -> "Session":
        """Return the Session whose project context activated this task."""
        return self._session

    @property
    def task(self) -> "TaskSubscriber":
        """Return the task that owns this activation."""
        return self._task

    @property
    def is_active(self) -> bool:
        """Return whether this activation may still create task-owned state."""
        return not self._retired

    def retire(self) -> None:
        """Retire this activation and all state currently owned by it."""
        if self._retired:
            return
        self._retired = True
        self._manager._retire_task_activation(self)

    def subscribe(
        self,
        event_types: EventType,
        timer_interval: float | None = None,
        initial_delay: float | None = None,
        once_interval: float | None = None,
        *,
        priority: bool = False,
    ) -> None:
        """Subscribe the owning task while this activation remains active."""
        if self.is_active:
            self._manager._subscribe(
                self._task,
                event_types,
                timer_interval,
                initial_delay,
                once_interval,
                priority=priority,
                activation=self,
            )

    async def unsubscribe(self) -> None:
        """Remove subscriptions owned by this activation."""
        self._manager._remove_activation_subscriptions(self)
        await self._manager._stop_timer_if_unused()

    async def resolved_flags(self) -> dict[str, Any]:
        """Return resolved flags for this activation's bound Session."""
        return await self._manager.resolved_flags(self._session)

    async def requires_flag(self, flag_name: str) -> bool:
        """Return whether one resolved flag is enabled for this task."""
        return await self._manager.requires_flag(flag_name, self._session)

    def get_cached_data(self, key: str) -> Any:
        """Read task-manager cache data visible to this activation."""
        return self._manager.get_cached_data(key)

    def set_cached_data(self, key: str, value: Any) -> None:
        """Store a value owned by this activation while it remains active."""
        self._manager._set_cached_data(key, value, activation=self)

    async def queue_instruction(self, instruction: str, priority: bool = False) -> None:
        """Queue an instruction owned by this activation."""
        await self._manager._queue_instruction(instruction, priority=priority, activation=self)

    async def queue_instruction_with_ack(
        self,
        content: str,
        max_retries: int = 3,
        *,
        on_dispatch: Callable[[], Awaitable[None]] | None = None,
    ) -> str:
        """Queue an acknowledgement-tracked instruction owned by this activation."""
        return await self._manager._queue_instruction_with_ack(
            content,
            max_retries=max_retries,
            on_dispatch=on_dispatch,
            activation=self,
        )

    async def acknowledge_instruction(self, instruction_id: str) -> None:
        """Acknowledge an instruction previously queued by this task."""
        await self._manager._acknowledge_instruction(instruction_id, activation=self)
