"""Project configuration management."""

import asyncio
from pathlib import Path
from typing import Optional

import yaml

from mcp_guide.file_lock import lock_update
from mcp_guide.models import _NAME_REGEX, Project


class ConfigManager:
    """Manager for project configuration file."""

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """Initialize config manager.

        Args:
            config_dir: Optional config directory for test isolation.
                       If None, uses default system config directory.
        """
        self._config_dir = config_dir
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Initialize config manager (only once)."""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    from mcp_guide.config_paths import get_config_file

                    self.config_file = get_config_file(self._config_dir)
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    if not self.config_file.exists():
                        self.config_file.write_text("projects: {}\n")
                    self._initialized = True

    async def get_or_create_project_config(self, name: str) -> Project:
        """Get project config or create if it doesn't exist.

        Args:
            name: Project name (alphanumeric, hyphens, underscores, 1-50 chars)

        Returns:
            Project configuration

        Raises:
            ValueError: If project name is invalid or empty
            OSError: If config file cannot be read/written
            yaml.YAMLError: If config file contains invalid YAML

        Note:
            This operation is atomic and async-safe due to file locking.
            If the project doesn't exist, a new one is created with default settings.
        """
        # Validate project name
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        if not _NAME_REGEX.match(name):
            raise ValueError(
                f"Invalid project name '{name}': must contain only alphanumeric characters, underscores, and hyphens"
            )

        await self._ensure_initialized()

        async def _get_or_create(file_path: Path) -> Project:
            try:
                content = file_path.read_text()
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            if name in projects:
                project_data = projects[name]
                try:
                    return Project(**project_data)
                except Exception as e:
                    raise ValueError(f"Invalid project data for '{name}' in {file_path}: {e}") from e

            # Create new project
            project = Project(name=name)
            projects[name] = self._project_to_dict(project)
            data["projects"] = projects

            try:
                file_path.write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

            return project

        return await lock_update(self.config_file, _get_or_create)

    async def save_project_config(self, project: Project) -> None:
        """Save project config to file.

        Args:
            project: Project configuration to save

        Raises:
            OSError: If config file cannot be read/written
            yaml.YAMLError: If config file contains invalid YAML

        Note:
            This operation is atomic and async-safe due to file locking.
        """
        await self._ensure_initialized()

        async def _save(file_path: Path) -> None:
            try:
                content = file_path.read_text()
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            projects[project.name] = self._project_to_dict(project)
            data["projects"] = projects

            try:
                file_path.write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _save)

    async def list_projects(self) -> list[str]:
        """List all project names."""
        await self._ensure_initialized()

        async def _list(file_path: Path) -> list[str]:
            try:
                content = file_path.read_text()
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            return list(data.get("projects", {}).keys())

        return await lock_update(self.config_file, _list)

    async def rename_project(self, old_name: str, new_name: str) -> None:
        """Rename a project."""
        # Validate new name
        if not new_name or not new_name.strip():
            raise ValueError("Project name cannot be empty")
        if not _NAME_REGEX.match(new_name):
            raise ValueError(
                f"Invalid project name '{new_name}': must contain only "
                "alphanumeric characters, underscores, and hyphens"
            )

        await self._ensure_initialized()

        async def _rename(file_path: Path) -> None:
            try:
                content = file_path.read_text()
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            if old_name not in projects:
                raise ValueError(f"Project not found: {old_name}")
            if new_name in projects:
                raise ValueError(f"Project already exists: {new_name}")

            projects[new_name] = projects.pop(old_name)
            projects[new_name]["name"] = new_name
            data["projects"] = projects

            try:
                file_path.write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _rename)

    async def delete_project(self, name: str) -> None:
        """Delete a project."""
        await self._ensure_initialized()

        async def _delete(file_path: Path) -> None:
            try:
                content = file_path.read_text()
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            if name not in projects:
                raise ValueError(f"Project not found: {name}")

            del projects[name]
            data["projects"] = projects

            try:
                file_path.write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _delete)

    def _project_to_dict(self, project: Project) -> dict[str, object]:
        """Convert Project to dict for YAML serialization."""
        return {
            "name": project.name,
            "categories": [
                {"name": c.name, "dir": c.dir, "patterns": c.patterns, "description": c.description}
                for c in project.categories
            ],
            "collections": [
                {
                    "name": c.name,
                    "categories": c.categories,
                    "description": c.description,
                }
                for c in project.collections
            ],
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }


# Module-level singleton instance (lazy initialization)
_config_manager: Optional[ConfigManager] = None
_init_lock = asyncio.Lock()


async def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance.

    Returns:
        The singleton ConfigManager instance

    Note:
        This is the preferred way to access the ConfigManager.
        The instance is created on first access (lazy initialization).
    """
    global _config_manager
    async with _init_lock:
        if _config_manager is None:
            _config_manager = ConfigManager()
    return _config_manager


# Public API
__all__ = ["ConfigManager", "get_config_manager"]
