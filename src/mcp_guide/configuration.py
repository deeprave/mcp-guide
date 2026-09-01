"""Runtime-owned configuration persistence and publication."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml
from anyio import Path as AsyncPath

from mcp_guide.core.file_reader import read_file_content
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.feature_flags.types import FeatureValue, to_raw_feature_value
from mcp_guide.file_lock import lock_update
from mcp_guide.models import _NAME_REGEX, Project
from mcp_guide.utils.project_hash import (
    calculate_project_hash,
    extract_name_from_key,
    generate_project_key,
)
from mcp_guide.watchers.config_watcher import ConfigWatcher

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


class _ConfigManagerCore:
    """Persistence implementation for the runtime-owned configuration service."""

    def __init__(self, config_dir: Optional[str] = None, docroot: str | Path | None = None) -> None:
        """Initialize config manager."""
        self.__config_dir = config_dir
        self.__docroot: Optional[str] = None
        self.__feature_flags: Optional[dict[str, Any]] = None
        # Import here to avoid circular dependency with config_paths module
        from mcp_guide.config_paths import get_config_file

        self.config_file = get_config_file(self.__config_dir).resolve()
        self._explicit_docroot = Path(docroot).expanduser().resolve() if docroot else None

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

            await install_and_create_config(file_path, self._explicit_docroot)
            return await read_file_content(file_path)

    async def get_docroot(self) -> str:
        """Get cached docroot value."""
        if self.__docroot is None:

            async def _get_docroot(file_path: Path) -> str:
                content = await self.get_or_create_config(file_path)
                data = yaml.safe_load(content) or {}
                configured_docroot = data.get("docroot")
                if not isinstance(configured_docroot, str) or not configured_docroot.strip():
                    default = self._explicit_docroot or (file_path.parent.resolve() / "docs")
                    docroot = str(default)
                    data["docroot"] = docroot
                    await AsyncPath(file_path).write_text(yaml.dump(data))
                else:
                    docroot = configured_docroot
                return docroot

            self.__docroot = await lock_update(self.config_file, _get_docroot)
        return self.__docroot

    async def get_feature_flags(self) -> dict[str, FeatureValue]:
        """Get feature flags."""
        if self.__feature_flags is None:

            async def _get_flags(file_path: Path) -> dict[str, FeatureValue]:
                content = await self.get_or_create_config(file_path)
                data = yaml.safe_load(content)
                raw_flags = data.get("feature_flags", {}) if data else {}
                return {key: FeatureValue.from_raw(value) for key, value in raw_flags.items()}

            self.__feature_flags = await lock_update(self.config_file, _get_flags)
            logger.trace(f"get_feature_flags: loaded from disk, flags={self.__feature_flags!r}")
        return self.__feature_flags

    async def set_feature_flag(self, flag_name: str, value: FeatureValue) -> None:
        """Set a feature flag."""

        async def _set_flag(file_path: Path) -> None:
            content = await self.get_or_create_config(file_path)
            data = yaml.safe_load(content)
            if "feature_flags" not in data:
                data["feature_flags"] = {}
            data["feature_flags"][flag_name] = to_raw_feature_value(value)
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
        if "project_flags" in data:
            data["project_flags"] = {
                flag_name: to_raw_feature_value(flag_value) for flag_name, flag_value in project.project_flags.items()
            }
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

    async def get_or_create_project_config(self, name: str, *, root_path: Path | None = None) -> tuple[str, Project]:
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
        if root_path is None:
            raise ValueError("Project configuration resolution requires an explicitly bound root path")

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

            # An explicit root binding has an unambiguous configuration
            # identity. It must never fall through to the historical
            # name-only lookup, which could select another root's project.
            if root_path is not None:
                root_hash = calculate_project_hash(str(root_path))
                expected_key = generate_project_key(name, root_hash)
                project_data = projects.get(expected_key)
                if isinstance(project_data, dict) and project_data.get("hash") == root_hash:
                    project_data_copy = dict(project_data)
                    project_data_copy["key"] = expected_key
                    return expected_key, self._dict_to_project(project_data_copy)
                project_key, project = await self._create_new_project(name, file_path, data, root_path=root_path)
                if yaml.dump(data) != original_data:
                    await AsyncPath(file_path).write_text(yaml.dump(data))
                return project_key, project

            raise AssertionError("root_path is required before configuration lookup")

        self._ensure_config_dir()
        return await lock_update(self.config_file, _get_or_create)

    async def get_project_config_for_root(self, name: str, root_path: Path | None) -> Project | None:
        """Return an existing strictly matching project configuration.

        This non-creating lookup is used while applying a configuration
        publication. It must not recreate an entry removed or invalidated
        by an external writer.
        """
        if root_path is None:
            return None

        async def _get_existing(file_path: Path) -> Project | None:
            content = await self.get_or_create_config(file_path)
            data = yaml.safe_load(content) or {}
            projects = data.get("projects", {})
            if not isinstance(projects, dict):
                return None
            root_hash = calculate_project_hash(str(root_path))
            expected_key = generate_project_key(name, root_hash)
            project_data = projects.get(expected_key)
            if not isinstance(project_data, dict) or project_data.get("hash") != root_hash:
                return None
            project_data_copy = dict(project_data)
            project_data_copy["key"] = expected_key
            return self._dict_to_project(project_data_copy)

        return await lock_update(self.config_file, _get_existing)

    async def _create_new_project(
        self, name: str, file_path: Path, data: dict[str, Any], *, root_path: Path | None = None
    ) -> tuple[str, Project]:
        """Create a new project with hash."""
        if root_path is None:
            raise ValueError("Project creation requires an explicitly bound root path")
        current_path = str(root_path)

        project_hash = calculate_project_hash(current_path)
        project_key = generate_project_key(name, project_hash)
        project = Project(name=name, key=project_key, hash=project_hash)

        # Apply _default profile to new project if enabled
        from mcp_guide import session as session_module

        if session_module._enable_default_profile:
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

        cached_snapshot = getattr(self, "_snapshot", None)
        if cached_snapshot is not None:
            return self._projects_from_data(cached_snapshot.get("projects", {}))

        async def _read_all_projects(file_path: Path) -> dict[str, Project]:
            try:
                content = await self.get_or_create_config(file_path)
            except OSError as e:
                raise OSError(f"Failed to read config file {file_path}: {e}") from e

            try:
                data = yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in config file {file_path}: {e}") from e

            return self._projects_from_data(data.get("projects", {}))

        return await lock_update(self.config_file, _read_all_projects)

    def _projects_from_data(self, projects_data: Any) -> dict[str, Project]:
        """Return only strictly valid hash-suffixed project entries."""
        if not isinstance(projects_data, dict):
            return {}

        projects: dict[str, Project] = {}
        for project_key, project_data in projects_data.items():
            if not isinstance(project_key, str):
                logger.warning("Ignoring malformed project configuration key '%s'", project_key)
                continue

            if not isinstance(project_data, dict):
                logger.warning("Ignoring malformed project configuration '%s'", project_key)
                continue

            name = extract_name_from_key(project_key)
            stored_hash = project_data.get("hash")
            if not isinstance(stored_hash, str):
                logger.warning("Ignoring malformed project configuration '%s'", project_key)
                continue
            if project_key != generate_project_key(name, stored_hash):
                logger.warning("Ignoring project configuration with mismatched hash '%s'", project_key)
                continue

            project_data_copy = dict(project_data)
            project_data_copy["name"] = name
            project_data_copy["key"] = project_key
            projects[project_key] = self._dict_to_project(project_data_copy)

        return projects

    async def resolve_clone_source(self, source_name: str) -> tuple[Project | None, list[str]]:
        """Resolve a clone source, including one explicit hashless recovery key."""

        def _resolve(projects_data: Any) -> tuple[Project | None, list[str]]:
            if not isinstance(projects_data, dict):
                return None, []

            strict_projects = self._projects_from_data(projects_data)
            if source_name in strict_projects:
                return strict_projects[source_name], []

            # A caller that supplied an exact hash-suffixed key has already
            # selected its intended source; never silently broaden that into a
            # name lookup.
            if extract_name_from_key(source_name) != source_name:
                return None, []

            for project in strict_projects.values():
                if project.name == source_name:
                    return project, []

            # Ordinary list/select use the filtered public image, so hashless
            # keys never appear there. Clone still consults the unfiltered
            # on-disk map: if from_project equals a discarded YAML key (the
            # pre-hash project name), recover that entry so older configs can
            # still be cloned. A listed name or hash-suffixed key never
            # reaches this loop.
            for project_key, project_data in projects_data.items():
                if project_key != source_name or not isinstance(project_data, dict):
                    continue
                project_data_copy = dict(project_data)
                project_data_copy["name"] = source_name
                project_data_copy["key"] = source_name
                return self._dict_to_project(project_data_copy), []
            return None, []

        raw_projects_snapshot = getattr(self, "_raw_projects_snapshot", None)
        if raw_projects_snapshot is not None:
            return _resolve(raw_projects_snapshot)

        async def _read_source(file_path: Path) -> tuple[Project | None, list[str]]:
            content = await self.get_or_create_config(file_path)
            data = yaml.safe_load(content) or {}
            return _resolve(data.get("projects", {}))

        return await lock_update(self.config_file, _read_source)

    async def save_project_config(self, project_key: str, project: Project) -> None:
        """Save project config using provided project key."""
        if not project.hash or project_key != generate_project_key(project.name, project.hash):
            raise ValueError("Project configuration key must match the project's name and root hash")

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


class ConfigManager(_ConfigManagerCore):
    """Runtime-owned configuration service.

    ``GuideRuntime`` owns the production instance and supplies it to every
    Session. It owns the single configuration-file watcher and publishes
    changes to all registered Sessions.
    """

    def __init__(self, config_dir: Optional[str] = None, docroot: str | Path | None = None) -> None:
        super().__init__(config_dir=config_dir, docroot=docroot)
        self._sessions: set[Session] = set()
        self._watcher: ConfigWatcher | None = None
        self._watcher_lock = asyncio.Lock()
        self._image_lock = asyncio.Lock()
        self._publication_lock = asyncio.Lock()
        self._snapshot: dict[str, Any] | None = None
        self._raw_projects_snapshot: dict[str, Any] = {}

    def register_session(self, session: Session) -> None:
        """Register a Session for configuration-change publication."""
        self._sessions.add(session)

    def unregister_session(self, session: Session) -> None:
        """Stop publishing changes to a cleaned-up Session."""
        self._sessions.discard(session)

    async def start(self) -> None:
        """Start the one shared watcher after runtime configuration is ready."""
        async with self._watcher_lock:
            if self._watcher is not None and self._watcher.is_running():
                return
            self._ensure_config_dir()
            await self._replace_snapshot()
            # Docroot is process-global operational state. Resolve it once at
            # runtime start and retain that effective value until restart.
            await self.get_docroot()
            self._watcher = ConfigWatcher(str(self.config_file), callback=self._on_external_change, poll_interval=1.0)
            await self._watcher.start()

    async def stop(self) -> None:
        """Stop the shared watcher during GuideRuntime shutdown."""
        async with self._watcher_lock:
            if self._watcher is not None:
                await self._watcher.stop()
                self._watcher = None

    async def _read_snapshot(self) -> dict[str, Any]:
        """Read a complete validated configuration snapshot under the file lock."""

        async def _read(file_path: Path) -> dict[str, Any]:
            content = await self.get_or_create_config(file_path)
            data = yaml.safe_load(content) or {}
            if not isinstance(data, dict):
                raise ValueError("Guide configuration must be a YAML mapping")
            if "feature_flags" in data and not isinstance(data["feature_flags"], dict):
                raise ValueError("Guide configuration feature_flags must be a mapping")
            if "projects" in data and not isinstance(data["projects"], dict):
                raise ValueError("Guide configuration projects must be a mapping")
            # Keep a complete *validated* runtime snapshot. Invalid legacy or
            # malformed entries stay on disk but are deliberately excluded
            # from every runtime lookup and publication calculation.
            raw_projects = data.get("projects", {})
            self._raw_projects_snapshot = dict(raw_projects) if isinstance(raw_projects, dict) else {}
            valid_projects = self._projects_from_data(raw_projects)
            data["projects"] = {key: self._project_to_dict(project) for key, project in valid_projects.items()}
            return data

        self._ensure_config_dir()
        return await lock_update(self.config_file, _read)

    async def _replace_snapshot(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Replace the runtime cache with one current complete snapshot."""
        current = await self._read_snapshot()
        previous = self._snapshot or {}
        self._snapshot = current
        return previous, current

    @staticmethod
    def _changed_project_identities(previous: dict[str, Any], current: dict[str, Any]) -> set[tuple[str, str]]:
        """Return strict project identities whose persisted entries changed."""
        old_projects = previous.get("projects", {})
        new_projects = current.get("projects", {})
        if not isinstance(old_projects, dict) or not isinstance(new_projects, dict):
            return set()

        changed: set[tuple[str, str]] = set()
        for key in set(old_projects) | set(new_projects):
            if not isinstance(key, str):
                continue
            if old_projects.get(key) == new_projects.get(key):
                continue
            project_data = new_projects.get(key, old_projects.get(key))
            if not isinstance(project_data, dict):
                continue
            stored_hash = project_data.get("hash")
            if not isinstance(stored_hash, str):
                continue
            try:
                name = extract_name_from_key(key)
            except ValueError:
                continue
            if key == generate_project_key(name, stored_hash):
                changed.add((name, stored_hash))
        return changed

    async def _publish_snapshot_delta(self, previous: dict[str, Any], current: dict[str, Any]) -> None:
        """Publish only Sessions affected by a complete configuration diff."""
        global_changed = previous.get("feature_flags", {}) != current.get("feature_flags", {})
        changed_projects = self._changed_project_identities(previous, current)
        if not global_changed and not changed_projects:
            return

        if global_changed:
            self._invalidate_feature_flags()

        for session in list(self._sessions):
            project_changed = session.active_configuration_identity in changed_projects
            if not global_changed and not project_changed:
                continue
            try:
                await session._on_shared_config_changed(global_changed=global_changed, project_changed=project_changed)
            except Exception as error:
                logger.debug("Failed to publish configuration change to a Session: %s", error, exc_info=True)

    async def _refresh_and_publish(self) -> None:
        """Load, replace, diff, and publish a shared configuration update once."""
        async with self._publication_lock:
            async with self._image_lock:
                previous, current = await self._replace_snapshot()
            await self._publish_snapshot_delta(previous, current)

    async def _on_external_change(self, _path: str) -> None:
        """Publish only an externally observed snapshot that differs from the cache."""
        await self._refresh_and_publish()

    async def get_docroot(self) -> str:
        """Read process configuration through the coordinated in-memory image."""
        async with self._image_lock:
            return await super().get_docroot()

    async def get_feature_flags(self) -> dict[str, FeatureValue]:
        """Read feature flags through the coordinated in-memory image."""
        async with self._image_lock:
            return await super().get_feature_flags()

    async def get_all_project_configs(self) -> dict[str, Project]:
        """Read project configurations through the coordinated in-memory image."""
        async with self._image_lock:
            return await super().get_all_project_configs()

    async def get_or_create_project_config(self, name: str, *, root_path: Path | None = None) -> tuple[str, Project]:
        """Resolve a root-bound project through the authoritative shared image."""
        async with self._publication_lock:
            async with self._image_lock:
                await self._replace_snapshot()
                project_key, project = await super().get_or_create_project_config(name, root_path=root_path)
                previous, current = await self._replace_snapshot()
            await self._publish_snapshot_delta(previous, current)
        return project_key, project

    async def get_project_config_for_root(self, name: str, root_path: Path | None) -> Project | None:
        """Read an existing root-bound project from the authoritative image."""
        if root_path is None:
            return None

        async with self._image_lock:
            if self._snapshot is None:
                await self._replace_snapshot()
            assert self._snapshot is not None
            root_hash = calculate_project_hash(str(root_path))
            project_key = generate_project_key(name, root_hash)
            project_data = self._snapshot.get("projects", {}).get(project_key)
            if not isinstance(project_data, dict) or project_data.get("hash") != root_hash:
                return None
            project_data_copy = dict(project_data)
            project_data_copy["key"] = project_key
            return self._dict_to_project(project_data_copy)

    async def resolve_clone_source(self, source_name: str) -> tuple[Project | None, list[str]]:
        """Resolve clone sources through the coordinated in-memory image."""
        async with self._image_lock:
            return await super().resolve_clone_source(source_name)

    async def set_feature_flag(self, flag_name: str, value: FeatureValue) -> None:
        async with self._publication_lock:
            async with self._image_lock:
                await self._replace_snapshot()
                await super().set_feature_flag(flag_name, value)
                previous, current = await self._replace_snapshot()
            await self._publish_snapshot_delta(previous, current)

    async def remove_feature_flag(self, flag_name: str) -> None:
        async with self._publication_lock:
            async with self._image_lock:
                await self._replace_snapshot()
                await super().remove_feature_flag(flag_name)
                previous, current = await self._replace_snapshot()
            await self._publish_snapshot_delta(previous, current)

    async def save_project_config(self, project_key: str, project: Project) -> None:
        async with self._publication_lock:
            async with self._image_lock:
                await self._replace_snapshot()
                await super().save_project_config(project_key, project)
                previous, current = await self._replace_snapshot()
            await self._publish_snapshot_delta(previous, current)
