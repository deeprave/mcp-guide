"""Project configuration management."""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    pass

import yaml
from anyio import Path as AsyncPath

from mcp_core.file_reader import read_file_content
from mcp_guide.file_lock import lock_update
from mcp_guide.models import _NAME_REGEX, DEFAULT_ALLOWED_PATHS, Project
from mcp_guide.utils.project_hash import (
    calculate_project_hash,
    extract_name_from_key,
    generate_project_key,
)

logger = logging.getLogger(__name__)


class DocrootError(RuntimeError):
    """Raised when docroot cannot be created or is invalid."""

    pass


class ConfigManager:
    """Manager for project configuration file.

    IMPORTANT: This class should ONLY be instantiated and owned by the Session class.
    No other code should create ConfigManager instances directly or indirectly.

    The Session class is the sole owner of ConfigManager and provides controlled
    access to configuration operations through its public methods:
    - session.get_project() - Get current project config
    - session.update_config() - Update current project config
    - session.get_all_projects() - Get all projects atomically
    - session.save_project() - Save a project config

    Direct instantiation of ConfigManager outside of Session is a violation of
    encapsulation and should be avoided.
    """

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """Initialize config manager.

        Args:
            config_dir: Optional config directory for test isolation.
                       If None, uses default system config directory.

        Warning:
            This should only be called by Session.__init__().
            Do not instantiate ConfigManager directly.
        """
        self._config_dir = config_dir
        self._lock = asyncio.Lock()
        self._initialized = False
        self._docroot: Optional[str] = None
        self._cached_global_flags: Optional[dict[str, Any]] = None

    async def _ensure_initialized(self) -> None:
        """Initialize config manager (only once)."""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    from mcp_guide.config_paths import get_config_file, get_docroot

                    self.config_file = get_config_file(self._config_dir)
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    if not self.config_file.exists():
                        default_docroot = str(get_docroot(self._config_dir))
                        await AsyncPath(self.config_file).write_text(f"docroot: {default_docroot}\nprojects: {{}}\n")
                        self._docroot = default_docroot
                    else:
                        # Read docroot from existing config
                        content = await read_file_content(self.config_file)
                        data = yaml.safe_load(content)
                        self._docroot = data.get("docroot", str(get_docroot(self._config_dir)))

                    # Validate and create docroot
                    docroot_path = Path(self._docroot).expanduser()

                    if not docroot_path.exists():
                        try:
                            docroot_path.mkdir(parents=True, exist_ok=True)
                            logger.info(f"Created docroot directory: {docroot_path}")
                        except (PermissionError, OSError) as e:
                            logger.error(f"FATAL: Failed to create docroot directory '{docroot_path}': {e}")
                            raise DocrootError(f"Failed to create docroot directory '{docroot_path}': {e}") from e
                    elif not docroot_path.is_dir():
                        logger.error(f"FATAL: Docroot path exists but is not a directory: {docroot_path}")
                        raise DocrootError(f"Docroot path exists but is not a directory: {docroot_path}")

                    self._initialized = True

    def _invalidate_global_flags_cache(self) -> None:
        """Invalidate the global flags cache."""
        self._cached_global_flags = None

    async def get_docroot(self) -> str:
        """Get cached docroot value.

        Returns:
            Docroot path as string (may contain ~ or ${VAR})

        Raises:
            ValueError: If initialization fails
        """
        await self._ensure_initialized()
        return self._docroot or ""

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
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            # Search for project by display name (not key)
            found_project = None

            for key, project_data in projects.items():
                # Check if this project matches the requested name
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == name:
                    found_project = project_data
                    break

            if found_project:
                try:
                    # Don't pass name as kwarg since it's already in the data
                    return Project(**found_project)
                except Exception as e:
                    raise ValueError(f"Invalid project data for '{name}' in {file_path}: {e}") from e

            # Create new project
            # Calculate hash for current project path
            try:
                from mcp_guide.mcp_context import resolve_project_path

                current_path = await resolve_project_path()
            except ValueError:
                # Fallback to config file parent if project path unavailable
                current_path = str(file_path.parent.resolve())

            project_hash = calculate_project_hash(current_path)

            # Create project with hash and key
            project_key = generate_project_key(name, project_hash)
            project = Project(name=name, key=project_key, hash=project_hash)
            projects[project_key] = self._project_to_dict(project)
            data["projects"] = projects

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

            return project

        return await lock_update(self.config_file, _get_or_create)

    async def get_all_project_configs(self) -> dict[str, Project]:
        """Get all project configurations as a snapshot.

        This operation returns all projects at a point in time and does not create
        any projects. Uses file locking to ensure consistency. May write to the
        configuration file during legacy format migration.

        Returns:
            Dictionary mapping project names to Project objects

        Raises:
            OSError: If config file cannot be read
            yaml.YAMLError: If config file contains invalid YAML
            ValueError: If any project data is invalid
        """
        await self._ensure_initialized()

        async def _read_all_projects(file_path: Path) -> dict[str, Project]:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects_data = data.get("projects", {})
            projects: dict[str, Project] = {}

            # Check if migration is needed (legacy format detection)
            needs_migration = self._needs_migration(projects_data)

            if needs_migration:
                # Migrate legacy format to hash-based keys
                projects_data = await self._migrate_projects(projects_data, file_path)
                # Update the data dict for saving
                data["projects"] = projects_data

                # Save immediately to avoid data loss if subsequent processing fails
                try:
                    await AsyncPath(file_path).write_text(yaml.dump(data))
                    logger.info(f"Configuration migrated to hash-based format at {file_path}")
                except OSError as e:
                    raise OSError(f"Failed to write migrated config file {file_path}: {e}") from e

            for name, project_data in projects_data.items():
                try:
                    # Extract display name from potentially hash-suffixed key
                    display_name = extract_name_from_key(name)

                    # Create project data with correct name and key
                    project_data_copy = dict(project_data)
                    project_data_copy["name"] = display_name  # Ensure name matches display name
                    project_data_copy["key"] = name  # Set the project key

                    # Use original key to preserve all projects (including duplicates by name)
                    projects[name] = Project(**project_data_copy)
                except Exception as e:
                    raise ValueError(f"Invalid project data for '{name}': {e}") from e

            return projects

        return await lock_update(self.config_file, _read_all_projects)

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
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            # Generate hash-based key for the project
            # Calculate hash if not present
            if not project.hash:
                current_path = str(file_path.parent.resolve())
                project_hash = calculate_project_hash(current_path)
                # Create updated project with hash
                from dataclasses import replace

                project_with_hash = replace(project, hash=project_hash)
            else:
                project_with_hash = project
                project_hash = project.hash

            # Generate hash-based key
            project_key = generate_project_key(project.name, project_hash)

            # Remove old entries with same display name but different hash
            keys_to_remove = []
            for key in projects.keys():
                if extract_name_from_key(key) == project.name and key != project_key:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del projects[key]

            # Save with hash-based key
            projects[project_key] = self._project_to_dict(project_with_hash)
            data["projects"] = projects

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _save)

    async def list_projects(self) -> list[str]:
        """List all project names."""
        await self._ensure_initialized()

        async def _list(file_path: Path) -> list[str]:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            # Extract display names from project data
            project_names = []
            for key, project_data in projects.items():
                # Get name from project data if available, otherwise extract from key
                name = project_data.get("name", extract_name_from_key(key))
                project_names.append(name)

            return project_names

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
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            # Find project by display name
            old_key = None
            old_project_data = None

            for key, project_data in projects.items():
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == old_name:
                    old_key = key
                    old_project_data = project_data
                    break

            if not old_key:
                raise ValueError(f"Project not found: {old_name}")

            # Check if new name already exists
            for key, project_data in projects.items():
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == new_name:
                    raise ValueError(f"Project already exists: {new_name}")

            # Update project data with new name
            if old_project_data is not None:
                old_project_data["name"] = new_name

                # Generate new key with same hash but new name
                project_hash = old_project_data.get("hash")
                if project_hash:
                    new_key = generate_project_key(new_name, project_hash)
                else:
                    # Fallback for legacy projects without hash
                    new_key = new_name

                # Remove old entry and add new one
                del projects[old_key]
                projects[new_key] = old_project_data
                data["projects"] = projects

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _rename)

    async def delete_project(self, name: str) -> None:
        """Delete a project."""
        await self._ensure_initialized()

        async def _delete(file_path: Path) -> None:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})

            # Find project by display name
            key_to_delete = None
            for key, project_data in projects.items():
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == name:
                    key_to_delete = key
                    break

            if not key_to_delete:
                raise ValueError(f"Project not found: {name}")

            del projects[key_to_delete]
            data["projects"] = projects

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _delete)

    def _project_to_dict(self, project: Project) -> dict[str, object]:
        """Convert Project to dict for YAML serialization."""
        result: dict[str, object] = {
            "name": project.name,
            "categories": {
                name: {
                    k: v
                    for k, v in {
                        "dir": category.dir,
                        "patterns": category.patterns,
                        "description": category.description,
                    }.items()
                    if v is not None
                }
                for name, category in project.categories.items()
            },
            "collections": {
                name: {
                    k: v
                    for k, v in {"categories": collection.categories, "description": collection.description}.items()
                    if v is not None
                }
                for name, collection in project.collections.items()
            },
        }

        # Add hash if present
        if project.hash:
            result["hash"] = project.hash

        # Add project_flags if not empty
        if project.project_flags:
            result["project_flags"] = project.project_flags

        # Add allowed_paths if different from defaults
        if project.allowed_paths != DEFAULT_ALLOWED_PATHS:
            result["allowed_paths"] = project.allowed_paths

        return result

    async def get_feature_flags(self) -> dict[str, Any]:
        """Get global feature flags (cached).

        Returns:
            Dictionary of global feature flags
        """
        await self._ensure_initialized()

        if self._cached_global_flags is None:

            async def _get_flags(file_path: Path) -> dict[str, Any]:
                try:
                    content = await read_file_content(file_path)
                except OSError as e:
                    raise OSError(f"Failed to read config file {file_path}") from e

                try:
                    data = yaml.safe_load(content) or {}
                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Invalid YAML in config file {file_path}") from e

                flags = data.get("feature_flags", {})
                self._cached_global_flags = flags  # Cache the result
                return flags  # type: ignore[no-any-return]

            return await lock_update(self.config_file, _get_flags)

        return self._cached_global_flags

    async def set_feature_flag(self, flag_name: str, value: Any) -> None:
        """Set a global feature flag.

        Args:
            flag_name: Name of the flag
            value: Flag value
        """
        from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value

        if not validate_flag_name(flag_name):
            raise ValueError(f"Invalid flag name: {flag_name}")
        if not validate_flag_value(value):
            raise ValueError(f"Invalid flag value type: {type(value)}")

        await self._ensure_initialized()

        async def _set_flag(file_path: Path) -> None:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            feature_flags = data.get("feature_flags", {})
            feature_flags[flag_name] = value
            data["feature_flags"] = feature_flags

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _set_flag)
        self._invalidate_global_flags_cache()

    async def remove_feature_flag(self, flag_name: str) -> None:
        """Remove a global feature flag.

        Args:
            flag_name: Name of the flag to remove
        """
        from mcp_guide.feature_flags.validation import validate_flag_name

        if not validate_flag_name(flag_name):
            raise ValueError(f"Invalid flag name: {flag_name}")

        await self._ensure_initialized()

        async def _remove_flag(file_path: Path) -> None:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            feature_flags = data.get("feature_flags", {})
            if flag_name in feature_flags:
                del feature_flags[flag_name]
                data["feature_flags"] = feature_flags

                try:
                    await AsyncPath(file_path).write_text(yaml.dump(data))
                except OSError as e:
                    raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _remove_flag)
        self._invalidate_global_flags_cache()

    async def get_project_flags(self, project_name: str) -> dict[str, Any]:
        """Get project-specific feature flags.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary of project feature flags
        """
        await self._ensure_initialized()

        async def _get_flags(file_path: Path) -> dict[str, Any]:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            project_data = projects.get(project_name, {})
            return project_data.get("project_flags", {})  # type: ignore[no-any-return]

        return await lock_update(self.config_file, _get_flags)

    async def set_project_flag(self, project_name: str, flag_name: str, value: Any) -> None:
        """Set a project-specific feature flag.

        Args:
            project_name: Name of the project
            flag_name: Name of the flag
            value: Flag value
        """
        from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value

        if not validate_flag_name(flag_name):
            raise ValueError(f"Invalid flag name: {flag_name}")
        if not validate_flag_value(value):
            raise ValueError(f"Invalid flag value type: {type(value)}")

        await self._ensure_initialized()

        async def _set_flag(file_path: Path) -> None:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            if project_name not in projects:
                # Create project if it doesn't exist
                projects[project_name] = {}

            project_data = projects[project_name]
            project_flags = project_data.get("project_flags", {})
            project_flags[flag_name] = value
            project_data["project_flags"] = project_flags
            projects[project_name] = project_data
            data["projects"] = projects

            try:
                await AsyncPath(file_path).write_text(yaml.dump(data))
            except OSError as e:
                raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _set_flag)

    async def remove_project_flag(self, project_name: str, flag_name: str) -> None:
        """Remove a project-specific feature flag.

        Args:
            project_name: Name of the project
            flag_name: Name of the flag to remove
        """
        from mcp_guide.feature_flags.validation import validate_flag_name

        if not validate_flag_name(flag_name):
            raise ValueError(f"Invalid flag name: {flag_name}")

        await self._ensure_initialized()

        async def _remove_flag(file_path: Path) -> None:
            try:
                content = await read_file_content(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            projects = data.get("projects", {})
            if project_name in projects:
                project_data = projects[project_name]
                project_flags = project_data.get("project_flags", {})
                if flag_name in project_flags:
                    del project_flags[flag_name]
                    project_data["project_flags"] = project_flags
                    projects[project_name] = project_data
                    data["projects"] = projects

                    try:
                        await AsyncPath(file_path).write_text(yaml.dump(data))
                    except OSError as e:
                        raise OSError(f"Failed to write config file {file_path}: {e}") from e

        await lock_update(self.config_file, _remove_flag)

    def _needs_migration(self, projects_data: dict[str, Any]) -> bool:
        """Check if projects data needs migration from legacy format.

        Args:
            projects_data: Raw projects data from config file

        Returns:
            True if migration is needed (legacy format detected)
        """
        for key, project_data in projects_data.items():
            # Check if key has hash suffix (new format)
            if key != extract_name_from_key(key):
                continue  # Already new format

            # Check if project data has hash field
            if not project_data.get("hash"):
                return True  # Legacy format detected

        return False

    async def _migrate_projects(self, projects_data: dict[str, Any], file_path: Path) -> dict[str, Any]:
        """Migrate projects from legacy format to hash-based keys.

        Args:
            projects_data: Raw projects data from config file
            file_path: Config file path for current directory detection

        Returns:
            Migrated projects data with hash-based keys
        """

        migrated_data = {}
        # NOTE: During migration, we use the config file's parent directory as the project path.
        # This assumes the config file is in the project root. The hash will be verified and
        # updated when the project is next accessed from its actual working directory.
        current_path = str(file_path.parent.resolve())

        for old_key, project_data in projects_data.items():
            # Skip if already migrated (has hash suffix and hash field)
            if old_key != extract_name_from_key(old_key) and project_data.get("hash"):
                migrated_data[old_key] = project_data
                continue

            # Calculate hash for current path
            project_hash = calculate_project_hash(current_path)

            # Extract display name (handles both legacy and partially migrated keys)
            display_name = extract_name_from_key(old_key)

            # Generate new key with hash suffix
            new_key = generate_project_key(display_name, project_hash)

            # Add required fields to project data
            project_data = dict(project_data)  # Copy to avoid mutation
            project_data["hash"] = project_hash
            project_data["name"] = display_name  # Ensure name field exists

            migrated_data[new_key] = project_data
            logger.info(f"Migrated project '{old_key}' to '{new_key}' with hash {project_hash[:8]}")

        return migrated_data


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


# Public API (none)
__all__ = ()
