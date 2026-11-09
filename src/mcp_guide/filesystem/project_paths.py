"""Session-aware project path authorisation."""

from pathlib import Path
from typing import TYPE_CHECKING, Union

from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy

if TYPE_CHECKING:
    from mcp_guide.session import Session


async def resolve_project_path_policy(session: "Session") -> ReadWriteSecurityPolicy:
    """Build the sole path policy from static configuration and runtime defaults."""
    from mcp_guide.feature_flags.utils import resolve_effective_write_paths, resolve_runtime_default_read_paths
    from mcp_guide.utils.client_path import client_resolve
    from mcp_guide.worktree_task import WorktreeTask

    project = await session.get_project()
    worktree = session.worktree_path or session.bound_root_path
    if worktree is None:
        raise ValueError("Project context not available. Call set_project(path) first.")

    def resolve_client_path(path: Union[str, Path]) -> Path:
        return client_resolve(path, worktree)

    worktree_task = session.task_manager.get_task_by_type(WorktreeTask)
    active_worktrees = worktree_task.active_worktree_paths() if worktree_task is not None else set()
    policy = ReadWriteSecurityPolicy(
        write_allowed_paths=await resolve_effective_write_paths(session),
        additional_read_paths=[
            *project.additional_read_paths,
            *(await resolve_runtime_default_read_paths(session)),
            *active_worktrees,
        ],
        client_resolve=resolve_client_path,
    )
    policy.set_project_root(str(worktree))
    return policy
