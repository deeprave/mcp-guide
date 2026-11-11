"""Client-reported Git worktree inventory handling."""

import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_guide.decorators import task_register
from mcp_guide.feature_flags.constants import FLAG_HANDOFF_CONTEXT, FLAG_WORKFLOW_FILE
from mcp_guide.feature_flags.types import to_raw_feature_value
from mcp_guide.feature_flags.utils import get_resolved_flag_value, resolve_documents_path, resolve_effective_write_paths
from mcp_guide.handoff_context import HANDOFF_CONTEXT_LOCK_STALE_SECONDS, resolve_handoff_context
from mcp_guide.task_manager import EventType

if TYPE_CHECKING:
    from mcp_guide.task_manager.activation import TaskActivation
    from mcp_guide.task_manager.manager import EventResult


WORKTREE_INVENTORY_TTL_SECONDS = HANDOFF_CONTEXT_LOCK_STALE_SECONDS


@task_register
class WorktreeTask:
    """Retain client-reported worktree data for one worktree-bound session."""

    configuration_flags = frozenset({FLAG_HANDOFF_CONTEXT, FLAG_WORKFLOW_FILE})

    def __init__(self) -> None:
        self.activation: TaskActivation | None = None

    def get_name(self) -> str:
        return "WorktreeTask"

    async def start(self, activation: "TaskActivation") -> bool:
        resolved = resolve_handoff_context(
            await get_resolved_flag_value(activation.session, FLAG_HANDOFF_CONTEXT),
            documents_path=await resolve_documents_path(activation.session),
            allowed_write_paths=await resolve_effective_write_paths(activation.session),
        )
        if resolved.target is None or not resolved.eligible or resolved.format not in {"JSON", "YAML"}:
            return False
        configured_workflow_file = await get_resolved_flag_value(activation.session, FLAG_WORKFLOW_FILE)
        workflow_file = to_raw_feature_value(configured_workflow_file) if configured_workflow_file is not None else None
        if isinstance(workflow_file, str) and Path(workflow_file).name != workflow_file:
            return False
        self.activation = activation
        activation.subscribe(EventType.FS_FILE_CONTENT | EventType.FS_CWD)
        return True

    async def stop(self) -> None:
        self.activation = None

    def active_worktree_paths(self) -> set[str]:
        """Return the client-reported active checkout roots for read authorisation."""
        if self.activation is None or not self.is_inventory_current():
            return set()
        inventory = self.activation.get_cached_data("worktree_inventory")
        return set(inventory) if isinstance(inventory, set) else set()

    def template_inventory(self) -> dict[str, Any] | None:
        """Return fresh inventory data for template rendering, if available."""
        if self.activation is None or not self.is_inventory_current():
            return None
        observed_at = self.activation.get_cached_data("worktree_inventory_observed_at")
        return {"paths": sorted(self.active_worktree_paths()), "observed_at": observed_at}

    def is_inventory_current(self, *, now: float | None = None) -> bool:
        """Whether the client-reported worktree inventory is still current."""
        if self.activation is None:
            return False
        inventory = self.activation.get_cached_data("worktree_inventory")
        if not isinstance(inventory, set):
            return False
        observed_at = self.activation.get_cached_data("worktree_inventory_observed_at")
        if not isinstance(observed_at, (int, float)):
            return False
        age = (time.time() if now is None else now) - observed_at
        return 0 <= age <= WORKTREE_INVENTORY_TTL_SECONDS

    async def on_tool(self) -> None:
        pass

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        from mcp_guide.task_manager.manager import EventResult

        if event_type & EventType.FS_CWD:
            return self._validate_working_directory(data)
        if not event_type & EventType.FS_FILE_CONTENT:
            return None
        path = data.get("path")
        content = data.get("content")
        if not isinstance(path, str) or not isinstance(content, str) or self.activation is None:
            return None
        if path == ".git-worktrees.json":
            inventory = _parse_inventory(content)
            if inventory is None:
                return EventResult(result=False, message="Invalid worktree inventory: expected JSON worktree paths")
            self.activation.set_cached_data("worktree_inventory", inventory)
            self.activation.set_cached_data("worktree_inventory_observed_at", time.time())
            template_cache = getattr(self.activation.session, "template_cache", None)
            if template_cache is not None:
                template_cache.invalidate()
            return EventResult(result=True)
        return None

    def _validate_working_directory(self, data: dict[str, Any]) -> "EventResult | None":
        """Reject an unconfigured or differently bound client worktree."""
        from mcp_guide.task_manager.manager import EventResult

        if self.activation is None:
            return None
        reported = data.get("working_directory")
        expected = self.activation.session.worktree_path
        if not isinstance(reported, str) or expected is None:
            return None
        reported_path = Path(os.path.normpath(reported))
        expected_path = Path(os.path.normpath(str(expected)))
        root = self.activation.session.bound_root_path
        if root is None:
            return None
        if reported_path == expected_path or expected_path in reported_path.parents:
            return None
        inventory = self.active_worktree_paths()
        if not inventory:
            return EventResult(
                result=False,
                message=(
                    "The reported working directory differs from this session's bound worktree. "
                    "Run guide://_worktree/list to report the current Git worktree inventory before binding it."
                ),
            )
        if expected_path == root:
            inventory.add(str(root))
        configured_worktree = next(
            (Path(path) for path in inventory if reported_path == Path(path) or Path(path) in reported_path.parents),
            None,
        )
        if configured_worktree is None:
            return EventResult(
                result=False,
                message=(
                    "The reported working directory is not a configured Git worktree for this project. "
                    "Run guide://_worktree/list to report the current Git worktree inventory, then use a fresh "
                    "Guide interaction to bind that worktree."
                ),
            )
        if configured_worktree == expected_path:
            return None
        return EventResult(
            result=False,
            message=(
                "This Guide session is bound to a different worktree. Keep it unchanged. "
                f"Create a fresh Guide interaction, report `{reported}` as its working directory, then call "
                f"set_project(path=`{root}`, worktree=`{configured_worktree}`) without this session ID."
            ),
        )


def _parse_inventory(content: str) -> set[str] | None:
    """Read the client inventory's supported JSON path shapes."""
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    entries = value.get("worktrees") if isinstance(value, dict) else value
    if not isinstance(entries, list):
        return None
    paths: set[str] = set()
    for entry in entries:
        path = entry.get("path") if isinstance(entry, dict) else entry
        if not isinstance(path, str) or not path or not Path(path).is_absolute():
            return None
        paths.add(str(Path(os.path.normpath(path))))
    return paths
