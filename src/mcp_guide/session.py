"""Session management for per-project runtime state."""

import asyncio
import contextlib
import dataclasses
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union
from weakref import WeakKeyDictionary as _WeakKeyDictionary

import yaml
from anyio import Path as AsyncPath
from fastmcp import Context

from mcp_guide.core.file_reader import read_file_content
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.file_lock import lock_update
from mcp_guide.mcp_context import cache_mcp_globals, consume_bootstrap_mcp_data
from mcp_guide.models import _NAME_REGEX, Project
from mcp_guide.utils.project_hash import (
    calculate_project_hash,
    extract_name_from_key,
    generate_project_key,
)

# Module-level flag to control default profile application
_enable_default_profile = True

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo
    from mcp_guide.feature_flags.protocol import FeatureFlags
    from mcp_guide.render.cache import TemplateContextCache
    from mcp_guide.session_listener import SessionListener

# Keep old import for compatibility during transition
from mcp_guide.mcp_context import resolve_project_name, resolve_project_path
from mcp_guide.result import Result
from mcp_guide.watchers.config_watcher import ConfigWatcher

logger = get_logger(__name__)


class DocrootError(RuntimeError):
    """Raised when `docroot` cannot be created or is invalid."""

    pass


class Session:
    """Per-project runtime session with encapsulated configuration management."""

    @classmethod
    def _get_config_manager(cls, config_dir: Optional[str] = None) -> "Session._ConfigManager":
        """Get or create the singleton ConfigManager instance."""
        if not hasattr(cls, "_config_manager"):
            setattr(cls, "_config_manager", cls._ConfigManager(config_dir=config_dir))
        elif config_dir is not None:
            getattr(cls, "_config_manager").reconfigure(config_dir=config_dir)
        return getattr(cls, "_config_manager")

    class _ConfigManager:
        """Private ConfigManager implementation."""

        def __init__(self, config_dir: Optional[str] = None) -> None:
            """Initialize config manager."""
            self.__config_dir = config_dir
            self.__docroot: Optional[str] = None
            self.__feature_flags: Optional[dict[str, Any]] = None
            # Import here to avoid circular dependency with config_paths module
            from mcp_guide.config_paths import get_config_file

            self.config_file = get_config_file(self.__config_dir)

        def reconfigure(self, config_dir: Optional[str] = None) -> None:
            """Reconfigure existing ConfigManager for different config directory."""
            self.__config_dir = config_dir
            self.__docroot = None
            self.__feature_flags = None
            # Import here to avoid circular dependency with config_paths module
            from mcp_guide.config_paths import get_config_file

            self.config_file = get_config_file(self.__config_dir)

        def _invalidate_feature_flags(self) -> None:
            """Invalidate the feature flags cache."""
            logger.trace("Invalidating feature flags cache")
            self.__feature_flags = None

        def _ensure_config_dir(self) -> None:
            """Ensure config directory exists, creating it if necessary."""
            config_dir = self.config_file.parent
            if not config_dir.exists():
                try:
                    config_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.exception(f"Failed to create config directory {config_dir}: {e}")

        async def get_or_create_config(self, file_path: Path) -> str:
            """Read config, or install templates and create it on first run.

            Args:
                file_path: Path to config file

            Returns:
                Config file content as string

            Raises:
                PermissionError: Cannot read/write config file
                Other OSError: File system errors (not FileNotFoundError)
            """
            try:
                return await read_file_content(file_path)
            except FileNotFoundError:
                # First run - install templates and create config
                # Import here to avoid loading installer code unless needed
                from mcp_guide.installer.integration import install_and_create_config

                await install_and_create_config(file_path)
                return await read_file_content(file_path)

        async def get_docroot(self) -> str:
            """Get cached docroot value."""
            if self.__docroot is None:

                async def _get_docroot(file_path: Path) -> str:
                    from mcp_guide.config_paths import get_docroot as get_default_docroot

                    content = await self.get_or_create_config(file_path)
                    data = yaml.safe_load(content)
                    docroot: str = data.get("docroot", str(get_default_docroot(self.__config_dir)))
                    return docroot

                self.__docroot = await lock_update(self.config_file, _get_docroot)
            return self.__docroot

        async def client_resolve(self, path: Union[str, Path]) -> Path:
            """Resolve a path relative to the client's working directory.

            This method handles path resolution from the server's perspective when
            dealing with client filesystem paths. The server cannot use Path.resolve()
            directly since it doesn't have access to the client's filesystem.

            Args:
                path: Path to resolve (relative or absolute)

            Returns:
                Absolute Path object representing the resolved client path

            Examples:
                >>> await session.client_resolve(".guide.yaml")
                PosixPath('/home/username/project/.guide.yaml')

                >>> await session.client_resolve("../config.json")
                PosixPath('/home/username/config.json')
            """
            from mcp_guide.utils.client_path import client_resolve

            client_cwd = await resolve_project_path()
            return client_resolve(path, client_cwd)

        async def get_feature_flags(self) -> dict[str, Any]:
            """Get feature flags."""
            if self.__feature_flags is None:

                async def _get_flags(file_path: Path) -> dict[str, Any]:
                    content = await self.get_or_create_config(file_path)
                    data = yaml.safe_load(content)
                    return data.get("feature_flags", {}) if data else {}

                self.__feature_flags = await lock_update(self.config_file, _get_flags)
                logger.trace(f"get_feature_flags: loaded from disk, flags={self.__feature_flags!r}")
            return self.__feature_flags

        async def set_feature_flag(self, flag_name: str, value: Any) -> None:
            """Set a feature flag."""

            async def _set_flag(file_path: Path) -> None:
                content = await self.get_or_create_config(file_path)
                data = yaml.safe_load(content)
                if "feature_flags" not in data:
                    data["feature_flags"] = {}
                data["feature_flags"][flag_name] = value
                await AsyncPath(file_path).write_text(yaml.dump(data))

            await lock_update(self.config_file, _set_flag)
            self._invalidate_feature_flags()

        async def remove_feature_flag(self, flag_name: str) -> None:
            """Remove a feature flag."""

            async def _remove_flag(file_path: Path) -> None:
                content = await self.get_or_create_config(file_path)
                data = yaml.safe_load(content)
                if "feature_flags" in data and flag_name in data["feature_flags"]:
                    del data["feature_flags"][flag_name]
                    await AsyncPath(file_path).write_text(yaml.dump(data))

            await lock_update(self.config_file, _remove_flag)
            self._invalidate_feature_flags()

        @staticmethod
        def _is_legacy_format(projects: dict[str, Any]) -> bool:
            """Check if projects dict uses legacy format."""
            for key, project_data in projects.items():
                if not isinstance(project_data, dict):
                    continue
                # Legacy format lacks hash field
                if "hash" not in project_data:
                    return True
            return False

        @staticmethod
        def _project_to_dict(project: Project) -> dict[str, Any]:
            """Convert Project to dictionary for YAML storage.

            Strips the 'name' field from categories since it's redundant with the dict key.
            Converts exports dict keys from tuples to strings for YAML compatibility.
            """
            data = dataclasses.asdict(project)
            # Remove 'name' field from each category (it's redundant with the key)
            if "categories" in data:
                for category_data in data["categories"].values():
                    category_data.pop("name", None)
            # Convert exports tuple keys to strings for YAML
            if "exports" in data:
                data["exports"] = {
                    f"{expr}:{pat if pat is not None else ''}": exported
                    for (expr, pat), exported in data["exports"].items()
                }
            return data

        @staticmethod
        def _dict_to_project(project_data: dict[str, Any]) -> Project:
            """Convert dictionary to Project, setting category names from keys.

            Args:
                project_data: Dictionary with project data from YAML

            Returns:
                Project instance with category names set from dict keys
            """
            from mcp_guide.models.project import Category, ExportedTo

            # Make a copy to avoid modifying the input
            data = dict(project_data)

            # Set category names from dict keys
            if "categories" in data:
                categories_dict = {}
                for cat_name, cat_data in data["categories"].items():
                    # Ensure name is set from the key
                    cat_data_copy = dict(cat_data)
                    cat_data_copy["name"] = cat_name
                    categories_dict[cat_name] = Category(**cat_data_copy)
                data["categories"] = categories_dict

            # Convert exports string keys back to tuples
            if "exports" in data:
                exports_dict = {}
                for key_str, exported_data in data["exports"].items():
                    expr, _, pat = key_str.partition(":")
                    key = (expr, pat if pat else None)
                    exports_dict[key] = ExportedTo(**exported_data)
                data["exports"] = exports_dict

            return Project(**data)

        async def get_or_create_project_config(self, name: str) -> tuple[str, Project]:
            """Get project config or create if it doesn't exist.

            Returns:
                Tuple of (project_key, project) where project_key includes hash suffix
            """
            # Validate project name
            if not name or not name.strip():
                raise ValueError("Project name cannot be empty")
            if not _NAME_REGEX.match(name):
                raise ValueError(
                    f"Invalid project name '{name}': must contain only alphanumeric characters, underscores, and hyphens"
                )

            async def _get_or_create(file_path: Path) -> tuple[str, Project]:
                try:
                    content = await self.get_or_create_config(file_path)
                except OSError as e:
                    raise OSError(f"Failed to read config file {file_path}: {e}") from e

                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

                projects = data.get("projects", {})
                original_data = yaml.dump(data)

                # Early legacy detection
                if self._is_legacy_format(projects):
                    result = await self._migrate_and_load_project(name, file_path, data)
                else:
                    # Hash-based project resolution for non-legacy projects
                    with contextlib.suppress(ValueError, RuntimeError):
                        current_path = await resolve_project_path()
                        current_hash = calculate_project_hash(str(current_path))
                        expected_key = generate_project_key(name, current_hash)

                        # First try exact key match (most efficient)
                        if expected_key in projects:
                            project_data = projects[expected_key]
                            project_data_copy = dict(project_data)
                            project_data_copy["key"] = expected_key
                            return expected_key, self._dict_to_project(project_data_copy)

                        # Then try hash-based matching for projects with same name
                        for key, project_data in projects.items():
                            project_name = project_data.get("name", extract_name_from_key(key))
                            project_hash = project_data.get("hash")
                            if project_name == name and project_hash == current_hash:
                                project_data_copy = dict(project_data)
                                project_data_copy["key"] = key
                                return key, self._dict_to_project(project_data_copy)

                    # Optimized non-legacy loading (name-only fallback)
                    result = await self._load_existing_project(name, projects, file_path, data)

                # Write back if data was modified
                if yaml.dump(data) != original_data:
                    try:
                        await AsyncPath(file_path).write_text(yaml.dump(data))
                    except OSError as e:
                        raise OSError(f"Failed to write config file {file_path}: {e}") from e

                return result

            self._ensure_config_dir()
            return await lock_update(self.config_file, _get_or_create)

        async def _migrate_and_load_project(
            self, name: str, file_path: Path, data: dict[str, Any]
        ) -> tuple[str, Project]:
            """Handle legacy project migration once."""
            projects = data.get("projects", {})

            # Find and migrate legacy project
            for key, project_data in projects.items():
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == name:
                    # Calculate hash and create new key
                    try:
                        current_path_obj = await resolve_project_path()
                        current_path = str(current_path_obj)
                    except ValueError:
                        current_path = str(file_path.parent.resolve())

                    project_hash = calculate_project_hash(current_path)
                    new_key = generate_project_key(name, project_hash)

                    # Update project data
                    project_data["hash"] = project_hash
                    projects[new_key] = project_data
                    if new_key != key:
                        del projects[key]

                    # Update data structure - file write handled by caller's lock_update
                    data["projects"] = projects

                    project_data_copy = dict(project_data)
                    project_data_copy["key"] = new_key
                    return new_key, self._dict_to_project(project_data_copy)

            # Create new project if not found
            return await self._create_new_project(name, file_path, data)

        async def _load_existing_project(
            self, name: str, projects: dict[str, Any], file_path: Path, data: dict[str, Any]
        ) -> tuple[str, Project]:
            """Load existing non-legacy project."""
            # Search for project by display name
            for key, project_data in projects.items():
                project_name = project_data.get("name", extract_name_from_key(key))
                if project_name == name:
                    try:
                        project_data_copy = dict(project_data)
                        project_data_copy["key"] = key
                        return key, self._dict_to_project(project_data_copy)
                    except Exception as e:
                        raise ValueError(f"Invalid project data for '{name}' in {file_path}: {e}") from e

            # Create a new project if not found
            return await self._create_new_project(name, file_path, data)

        async def _create_new_project(self, name: str, file_path: Path, data: dict[str, Any]) -> tuple[str, Project]:
            """Create a new project with hash."""
            # Calculate hash for the current project path
            try:
                current_path_obj = await resolve_project_path()
                current_path = str(current_path_obj)
            except (ValueError, RuntimeError):
                current_path = str(file_path.parent.resolve())

            project_hash = calculate_project_hash(current_path)
            project_key = generate_project_key(name, project_hash)
            project = Project(name=name, key=project_key, hash=project_hash)

            # Apply _default profile to new project if enabled
            if _enable_default_profile:
                try:
                    from mcp_guide.models.profile import Profile

                    default_profile = await Profile.load("_default")
                    project = default_profile.apply_to_project(project)
                except (FileNotFoundError, ValueError) as e:
                    logger.debug(f"Default profile not applied: {e}")
                    # Continue without default profile

            projects = data.get("projects", {})
            projects[project_key] = self._project_to_dict(project)
            data["projects"] = projects

            # Data structure updated - file write handled by caller's lock_update
            return project_key, project

        # Add other ConfigManager methods here (abbreviated for space)
        async def get_all_project_configs(self) -> dict[str, Project]:
            """Get all project configurations as a snapshot."""

            async def _read_all_projects(file_path: Path) -> dict[str, Project]:
                try:
                    content = await self.get_or_create_config(file_path)
                except OSError as e:
                    raise OSError(f"Failed to read config file {file_path}: {e}") from e

                try:
                    data = yaml.safe_load(content) or {}
                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

                projects_data = data.get("projects", {})
                projects: dict[str, Project] = {}

                for project_key, project_data in projects_data.items():
                    try:
                        name = extract_name_from_key(project_key)
                        project_data_copy = dict(project_data)
                        project_data_copy["name"] = name
                        project_data_copy["key"] = project_key
                        projects[project_key] = self._dict_to_project(project_data_copy)
                    except Exception as e:
                        raise ValueError(f"Invalid project data for '{project_key}': {e}") from e

                return projects

            return await lock_update(self.config_file, _read_all_projects)

        async def save_project_config(self, project_key: str, project: Project) -> None:
            """Save project config using provided project key."""

            async def _save(file_path: Path) -> None:
                try:
                    content = await self.get_or_create_config(file_path)
                except OSError as e:
                    raise OSError(f"Failed to read config file {file_path}: {e}") from e

                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

                projects = data.get("projects", {})
                projects[project_key] = self._project_to_dict(project)
                data["projects"] = projects

                try:
                    await AsyncPath(file_path).write_text(yaml.dump(data))
                except OSError as e:
                    raise OSError(f"Failed to write config file {file_path}: {e}") from e

            self._ensure_config_dir()
            await lock_update(self.config_file, _save)

    @classmethod
    async def create_session(cls, project_name: str, *, _config_dir_for_tests: Optional[str] = None) -> "Session":
        """Create a new session with the project loaded.

        Args:
            project_name: Name of the project to load
            _config_dir_for_tests: Optional config directory for test isolation

        Returns:
            Session with project loaded

        Raises:
            InvalidProjectNameError: If project name is invalid
        """
        # Import here to avoid circular dependency with validation module
        from mcp_guide.validation import InvalidProjectNameError

        if not project_name or not project_name.strip():
            raise InvalidProjectNameError("Project name cannot be empty")
        if not _NAME_REGEX.match(project_name):
            raise InvalidProjectNameError(
                f"Project name '{project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

        config_manager = cls._get_config_manager(_config_dir_for_tests)
        _key, project = await config_manager.get_or_create_project_config(project_name)
        return cls(project, _config_dir_for_tests=_config_dir_for_tests)

    def __init__(self, project: Project, *, _config_dir_for_tests: Optional[str] = None):
        """Initialise a session with a loaded project. Use create_session() to create."""
        self.__project: Project = project
        self._project_dirty = False
        self._config_watcher: Optional[ConfigWatcher] = None
        self._watcher_task: Optional["asyncio.Task[None]"] = None
        self._listeners: list["SessionListener"] = []
        self._template_cache: Optional["TemplateContextCache"] = None
        self.command_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

        # MCP context fields (populated by cache_mcp_globals)
        self.roots: list[Any] = []
        self.agent_info: Optional["AgentInfo"] = None
        self.client_params: Optional[dict[str, Any]] = None

        # Initialize config manager with test directory if provided
        if _config_dir_for_tests is not None:
            self._get_config_manager(_config_dir_for_tests)

    @property
    def project_name(self) -> str:
        """Get the current project name."""
        return self.__project.name

    @property
    def template_cache(self) -> "TemplateContextCache":
        """Get or create the per-session template context cache."""
        if self._template_cache is None:
            from mcp_guide.render.cache import TemplateContextCache

            self._template_cache = TemplateContextCache()
            self.add_listener(self._template_cache)
        return self._template_cache

    async def switch_project(self, project_name: str) -> None:
        """Switch this session to a different project.

        Args:
            project_name: Name of the project to switch to

        Raises:
            InvalidProjectNameError: If project name is invalid
        """
        from mcp_guide.validation import InvalidProjectNameError

        if not project_name or not project_name.strip():
            raise InvalidProjectNameError("Project name cannot be empty")
        if not _NAME_REGEX.match(project_name):
            raise InvalidProjectNameError(
                f"Project name '{project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

        old_project = self.__project.name
        if project_name == old_project:
            return

        config_manager = self._get_config_manager()
        _key, project = await config_manager.get_or_create_project_config(project_name)
        self.__project = project
        self._project_dirty = False
        await self._notify_project_changed(old_project, project_name)

    def _setup_config_watcher(self) -> None:
        """Setup config file watcher for automatic reload on external changes."""
        try:
            # Wait for ConfigManager to be initialized
            async def _setup_watcher() -> None:
                config_manager = self._get_config_manager()
                if config_manager:
                    config_file_path = str(config_manager.config_file)
                    self._config_watcher = ConfigWatcher(
                        config_path=config_file_path, callback=self._on_config_file_changed, poll_interval=1.0
                    )
                    self._watcher_task = None
                    self._watcher_lock = asyncio.Lock()  # ty: ignore[unresolved-attribute]

            asyncio.create_task(_setup_watcher())
        except (asyncio.InvalidStateError, OSError, AttributeError) as e:
            logger.warning(f"Could not setup config watcher for {self.project_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error setting up config watcher for {self.project_name}: {e}")
            raise

    async def _ensure_watcher_started(self) -> None:
        """Ensure config watcher is started."""
        if self._config_watcher and hasattr(self, "_watcher_lock"):
            async with self._watcher_lock:  # ty: ignore[invalid-context-manager]
                if self._watcher_task is None or self._watcher_task.done():
                    self._watcher_task = asyncio.create_task(self._config_watcher.start())

    async def _on_config_file_changed(self, file_path: str) -> None:
        """Handle config file changes by marking project stale."""
        logger.warning(
            f"Configuration file changed externally: {file_path} - marking session {self.project_name} dirty"
        )
        self._project_dirty = True
        await self._notify_config_changed()

    def add_listener(self, listener: "SessionListener") -> None:
        """Add a session change listener."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    async def _notify_project_changed(self, old_project: str, new_project: str) -> None:
        """Notify all listeners of project change."""
        for listener in self._listeners:
            try:
                await listener.on_project_changed(self, old_project, new_project)
            except Exception as e:
                logger.debug(f"Project change listener notification failed: {e}")

    async def _notify_config_changed(self) -> None:
        """Notify all listeners of config change."""
        for listener in self._listeners:
            try:
                await listener.on_config_changed(self)
            except Exception as e:
                logger.debug(f"Config change listener notification failed: {e}")

    async def cleanup(self) -> None:
        """Cleanup session resources including config watcher."""
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watcher_task
            self._watcher_task = None

        if self._config_watcher:
            try:
                await self._config_watcher.stop()
            except Exception as e:
                logger.debug(f"Error stopping config watcher: {e}")
            self._config_watcher = None

    async def get_project(self) -> Project:
        """Get the current project configuration, reloading if stale."""
        await self._ensure_watcher_started()
        if self._project_dirty:
            await self.invalidate_cache()
        return self.__project

    async def update_config(self, updater: Callable[[Project], Project]) -> None:
        """Update project config using functional pattern."""
        project = await self.get_project()
        updated_project = updater(project)

        if project.key is None:
            raise ValueError("Project key not available")

        config_manager = self._get_config_manager()
        await config_manager.save_project_config(project.key, updated_project)
        self.__project = updated_project

        # Notify listeners of config change
        await self._notify_config_changed()

    async def get_docroot(self) -> str:
        """Get document root path for the project."""
        config_manager = self._get_config_manager()
        return await config_manager.get_docroot()

    async def get_all_projects(self) -> dict[str, Project]:
        """Get all project configurations atomically."""
        config_manager = self._get_config_manager()
        return await config_manager.get_all_project_configs()

    async def save_project(self, project: Project) -> None:
        """Save project configuration using project's key."""
        if project.key is None:
            raise ValueError("Project key not available")

        config_manager = self._get_config_manager()
        await config_manager.save_project_config(project.key, project)

        # Update cache only if saving the session's own project
        if self.__project is not None and project.key == self.__project.key:
            self.__project = project

        # Notify listeners of config change
        await self._notify_config_changed()

    async def invalidate_cache(self) -> None:
        """Reload the project configuration from disk."""
        name = self.__project.name
        config_manager = self._get_config_manager()
        _key, project = await config_manager.get_or_create_project_config(name)
        self.__project = project
        self._project_dirty = False

        # Setup config file watcher
        self._setup_config_watcher()

    async def get_feature_flags(self) -> dict[str, Any]:
        """Get global feature flags."""
        config_manager = self._get_config_manager()
        return await config_manager.get_feature_flags()

    async def set_feature_flag(self, flag_name: str, value: Any) -> None:
        """Set a global feature flag."""
        config_manager = self._get_config_manager()
        await config_manager.set_feature_flag(flag_name, value)

    async def remove_feature_flag(self, flag_name: str) -> None:
        """Remove a global feature flag."""
        config_manager = self._get_config_manager()
        await config_manager.remove_feature_flag(flag_name)

    def feature_flags(self) -> "FeatureFlags":
        """Get feature flags proxy."""
        from mcp_guide.feature_flags.feature_flags import FeatureFlags

        return FeatureFlags(self)

    def project_flags(self, project: Optional[str] = None) -> "FeatureFlags":
        """Get project feature flags proxy."""
        from mcp_guide.feature_flags.project_flags import ProjectFlags

        return ProjectFlags(self)

    @staticmethod
    async def get_project_config(name: str) -> Project:
        """Get project configuration by name.

        Args:
            name: Project name

        Returns:
            Project configuration
        """
        config_manager = Session._get_config_manager()
        _, project = await config_manager.get_or_create_project_config(name)
        return project


# ContextVar for async task-local session tracking
_active_session: ContextVar[Optional[Session]] = ContextVar("_active_session", default=None)

# Registry mapping MiddlewareServerSession → Session for cross-task lookup (e.g. notification handlers).
# WeakKeyDictionary ensures entries are removed automatically when the MCP session is GC'd.

_session_registry: "_WeakKeyDictionary[Any, Session]" = _WeakKeyDictionary()


def register_session(mcp_session: Any, session: Session) -> None:
    """Register a guide Session against its MiddlewareServerSession."""
    _session_registry[mcp_session] = session


def get_session_by_mcp_session(mcp_session: Any) -> Optional[Session]:
    """Look up a guide Session by its MiddlewareServerSession object."""
    return _session_registry.get(mcp_session)


async def get_or_create_session(
    ctx: Optional["Context"] = None,
    project_name: Optional[str] = None,
    *,
    _config_dir_for_tests: Optional[str] = None,
) -> Session:
    """Get or create session for project.

    Args:
        ctx: Optional MCP Context (for roots detection)
        project_name: Optional explicit project name (for initial creation)
        _config_dir_for_tests: Optional config directory for test isolation (keyword-only)

    Returns:
        Session (existing or newly created)

    Raises:
        ValueError: If project name cannot be determined
    """
    # Return existing session if one exists
    existing_session = _active_session.get()
    if existing_session is not None:
        # Update MCP context if available and agent not yet detected
        if ctx and existing_session.agent_info is None:
            await cache_mcp_globals(ctx)
        # Ensure registry is populated even if session was created without ctx
        if ctx is not None:
            try:
                register_session(ctx.session, existing_session)
            except (AttributeError, TypeError):
                pass
            except RuntimeError as exc:
                logger.warning("Failed to register guide session for cross-task lookup: %s", exc)
        return existing_session

    # Determine project name for new session
    if project_name is None:
        if ctx:
            await cache_mcp_globals(ctx)
        project_name = await resolve_project_name()

    # Create new session with project loaded
    session = await Session.create_session(project_name, _config_dir_for_tests=_config_dir_for_tests)

    # Transfer bootstrap MCP data to session
    roots, agent_info, client_params = consume_bootstrap_mcp_data()
    session.roots = roots
    session.agent_info = agent_info
    session.client_params = client_params

    # Register per-session startup instruction listener
    from mcp_guide.startup_listener import StartupInstructionListener

    session.add_listener(StartupInstructionListener())

    # Register per-session guide URI instruction listener
    from mcp_guide.guide_uri_listener import GuideUriListener

    session.add_listener(GuideUriListener())

    # Store in ContextVar
    set_current_session(session)

    # Register for cross-task lookup (e.g. notification handlers)
    if ctx is not None:
        try:
            register_session(ctx.session, session)
        except AttributeError:
            pass  # ctx.session not available in this context (e.g. tests)
        except (RuntimeError, TypeError) as exc:
            logger.warning("Failed to register guide session for cross-task lookup: %s", exc)

    # Notify listeners of initial project load
    await session._notify_project_changed("", session.project_name)

    return session


async def get_session(
    ctx: Optional["Context"] = None,
    *,
    project_name: Optional[str] = None,
    _config_dir_for_tests: Optional[str] = None,
) -> Session:
    """Get the current session, creating one if none exists.

    This is the primary entry point for session access. On first call it creates
    a session with auto-resolved project name and caches MCP context from ctx.
    On subsequent calls it returns the existing session.

    Args:
        ctx: Optional MCP Context (for roots detection on first creation)
        project_name: Optional explicit project name (for initial creation or set_project)
        _config_dir_for_tests: Optional config directory for test isolation

    Returns:
        The current Session (never None)
    """
    return await get_or_create_session(ctx, project_name, _config_dir_for_tests=_config_dir_for_tests)


def get_active_session() -> Optional[Session]:
    """Return the current session if one exists, without creating one.

    This is for internal use by code that runs during session creation
    (e.g. mcp_context bootstrap) where await get_session() would recurse.
    """
    return _active_session.get()


def set_current_session(session: Session) -> None:
    """Set the current session in ContextVar.

    Args:
        session: Session to store in the current async context
    """
    _active_session.set(session)


async def remove_current_session() -> None:
    """Clear the current session from ContextVar and cleanup its resources."""
    session = _active_session.get()
    if session is not None:
        await session.cleanup()
    _active_session.set(None)


async def set_project(project_name: str, ctx: Optional["Context"] = None) -> Result[Project]:
    """Set/load a project by name.

    Args:
        project_name: Name of the project to set/load
        ctx: Optional MCP Context for roots detection

    Returns:
        Result[Project]: Success with Project object, or failure with error

    Note:
        Creates or loads project configuration.
        Use when project cannot be auto-detected from context.
    """
    from mcp_guide.result_constants import ERROR_INVALID_NAME, ERROR_PROJECT_LOAD
    from mcp_guide.validation import InvalidProjectNameError

    try:
        session = await get_session(ctx=ctx)
        await session.switch_project(project_name)
        project = await session.get_project()
        return Result.ok(project)
    except (InvalidProjectNameError, ValueError) as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        return Result.failure(str(e), error_type=ERROR_PROJECT_LOAD)


async def list_all_projects(session: "Session", verbose: bool = False) -> Result[dict[str, Any]]:
    """List all available projects.

    This is a read-only operation that returns a snapshot of all projects.

    Args:
        verbose: If True, return full project details; if False, return names only
        session: Session for flag resolution

    Returns:
        Result with projects dict
    """
    from mcp_guide.models import format_project_data
    from mcp_guide.result_constants import ERROR_CONFIG_READ, ERROR_INVALID_NAME, ERROR_UNEXPECTED

    try:
        # Verbose: get all project configs in one atomic read
        all_projects = await session.get_all_projects()
        if not verbose:
            # For non-verbose, show project keys when there are name conflicts
            project_list = []
            name_counts: dict[str, int] = {}

            # Count occurrences of each display name
            for key, project in all_projects.items():
                name_counts[project.name] = name_counts.get(project.name, 0) + 1

            # Build the list with disambiguation
            for key in sorted(all_projects.keys()):
                project = all_projects[key]
                if name_counts[project.name] > 1:
                    # Multiple projects with same name - show key for disambiguation
                    project_list.append(f"{project.name} ({key})")
                else:
                    # Unique name - show just the display name
                    project_list.append(project.name)

            return Result.ok({"projects": project_list})

        projects_data = {}
        for name in sorted(all_projects.keys()):
            projects_data[name] = await format_project_data(all_projects[name], verbose=True, session=session)
        return Result.ok({"projects": projects_data})
    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error listing projects")
        return Result.failure(f"Error listing projects: {e}", error_type=ERROR_UNEXPECTED)
