"""Project feature flags implementation."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mcp_guide.models import Project
    from mcp_guide.session import Session

from .types import FeatureValue


class ProjectFlags:
    """Project feature flags implementation that uses Session's cached project."""

    def __init__(self, session: "Session"):
        self._session = session

    async def list(self) -> dict[str, FeatureValue]:
        """List all project flags."""
        project = await self._session.get_project()
        return project.project_flags

    async def get(self, flag_name: str, default: Optional[FeatureValue] = None) -> Optional[FeatureValue]:
        """Get a specific project flag value."""
        flags = await self.list()
        return flags.get(flag_name, default)

    async def set(self, flag_name: str, value: FeatureValue) -> None:
        """Set a project flag value."""
        from dataclasses import replace

        def updater(project: "Project") -> "Project":
            new_flags = {**project.project_flags, flag_name: value}
            return replace(project, project_flags=new_flags)

        await self._session.update_config(updater)

    async def remove(self, flag_name: str) -> None:
        """Remove a project flag."""
        from dataclasses import replace

        def updater(project: "Project") -> "Project":
            new_flags = {k: v for k, v in project.project_flags.items() if k != flag_name}
            return replace(project, project_flags=new_flags)

        await self._session.update_config(updater)
