"""Immutable contracts for configuration publication and session reconciliation."""

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import registered_flag_names
from mcp_guide.models import Category, Project
from mcp_guide.models.project import ExportedTo
from mcp_guide.utils.project_hash import generate_project_key


def _freeze(value: Any) -> Any:
    """Create a recursively immutable configuration value."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_freeze(item) for item in value)
    return deepcopy(value)


def _thaw(value: Any) -> Any:
    """Return a detached raw value for model and feature-flag construction."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw(item) for item in value}
    return deepcopy(value)


@dataclass(frozen=True)
class ProjectIdentity:
    """Strict persisted identity for a bound project configuration."""

    name: str
    root_hash: str


@dataclass(frozen=True)
class ConfigurationSnapshotDelta:
    """One changed validated configuration image published to GuideRuntime."""

    revision: int
    previous: Mapping[str, Any]
    current: Mapping[str, Any]
    changed_project_identities: frozenset[ProjectIdentity]

    def __post_init__(self) -> None:
        """Freeze publication images before they leave configuration ownership."""
        object.__setattr__(self, "previous", _freeze(self.previous))
        object.__setattr__(self, "current", _freeze(self.current))
        object.__setattr__(self, "changed_project_identities", frozenset(self.changed_project_identities))

    @property
    def global_flags_changed(self) -> bool:
        """Whether the persisted global feature-flag mapping changed."""
        return self.previous.get("feature_flags", {}) != self.current.get("feature_flags", {})


@dataclass(frozen=True)
class ConfigurationChanges:
    """Named effective differences relevant to one bound Session."""

    project_entry_changed: bool
    project_content_changed: bool
    global_flags: frozenset[str]
    project_flags: frozenset[str]
    categories: frozenset[str]
    collections: frozenset[str]
    resolved_flags: frozenset[str]

    @property
    def is_empty(self) -> bool:
        """Whether no consumer-visible effective value changed."""
        # Raw global changes are retained for diagnosis, but an effective
        # project override can mask them completely for this Session.
        return not any(
            (
                self.project_entry_changed,
                self.project_content_changed,
                self.project_flags,
                self.categories,
                self.collections,
                self.resolved_flags,
            )
        )


@dataclass(frozen=True)
class ConfigurationUpdate:
    """One consumer-ready effective configuration update for a bound Session."""

    revision: int
    identity: ProjectIdentity
    previous_project: Mapping[str, Any] | None
    current_project: Mapping[str, Any] | None
    previous_resolved_flags: Mapping[str, FeatureValue]
    current_resolved_flags: Mapping[str, FeatureValue]
    changes: ConfigurationChanges

    def __post_init__(self) -> None:
        """Freeze consumer views independently from Session-owned project state."""
        if self.previous_project is not None:
            object.__setattr__(self, "previous_project", _freeze(self.previous_project))
        if self.current_project is not None:
            object.__setattr__(self, "current_project", _freeze(self.current_project))
        object.__setattr__(self, "previous_resolved_flags", _freeze(self.previous_resolved_flags))
        object.__setattr__(self, "current_resolved_flags", _freeze(self.current_resolved_flags))


def _project_snapshot(snapshot: Mapping[str, Any], identity: ProjectIdentity) -> Mapping[str, Any] | None:
    projects = snapshot.get("projects", {})
    if not isinstance(projects, Mapping):
        return None
    project = projects.get(generate_project_key(identity.name, identity.root_hash))
    return project if isinstance(project, Mapping) and project.get("hash") == identity.root_hash else None


def _flags(snapshot: Mapping[str, Any]) -> dict[str, FeatureValue]:
    flags = snapshot.get("feature_flags", {})
    return (
        {name: FeatureValue.from_raw(_thaw(value)) for name, value in flags.items()}
        if isinstance(flags, Mapping)
        else {}
    )


def _project_flags(project: Mapping[str, Any] | None) -> dict[str, FeatureValue]:
    flags = project.get("project_flags", {}) if project is not None else {}
    return (
        {name: FeatureValue.from_raw(_thaw(value)) for name, value in flags.items()}
        if isinstance(flags, Mapping)
        else {}
    )


def _resolved_flags(snapshot: Mapping[str, Any], project: Mapping[str, Any] | None) -> dict[str, FeatureValue]:
    global_flags = _flags(snapshot)
    project_flags = _project_flags(project)
    return {
        name: value
        for name in registered_flag_names()
        if (value := resolve_flag(name, project_flags, global_flags)) is not None
    }


def project_from_snapshot(project: Mapping[str, Any] | None, identity: ProjectIdentity) -> Project | None:
    """Reconstruct one validated project from the supplied immutable image."""
    if project is None:
        return None
    values = _thaw(project)
    values["key"] = generate_project_key(identity.name, identity.root_hash)
    categories = values.get("categories")
    if isinstance(categories, dict):
        values["categories"] = {name: Category(**{**category, "name": name}) for name, category in categories.items()}
    exports = values.get("exports")
    if isinstance(exports, dict):
        values["exports"] = {
            (expression, pattern or None): ExportedTo(**exported)
            for key, exported in exports.items()
            for expression, _, pattern in (key.partition(":"),)
        }
    return Project(**values)


def derive_configuration_update(delta: ConfigurationSnapshotDelta, identity: ProjectIdentity) -> ConfigurationUpdate:
    """Project one configuration snapshot delta into one bound Session's state."""
    previous_project = _project_snapshot(delta.previous, identity)
    current_project = _project_snapshot(delta.current, identity)
    previous_global_flags = _flags(delta.previous)
    current_global_flags = _flags(delta.current)
    previous_resolved = _resolved_flags(delta.previous, previous_project)
    current_resolved = _resolved_flags(delta.current, current_project)
    previous_project_flags = _project_flags(previous_project)
    current_project_flags = _project_flags(current_project)
    previous_categories = previous_project.get("categories", {}) if previous_project is not None else {}
    current_categories = current_project.get("categories", {}) if current_project is not None else {}
    previous_collections = previous_project.get("collections", {}) if previous_project is not None else {}
    current_collections = current_project.get("collections", {}) if current_project is not None else {}
    changes = ConfigurationChanges(
        project_entry_changed=(previous_project is None) != (current_project is None),
        project_content_changed=previous_project != current_project,
        global_flags=frozenset(
            name
            for name in set(previous_global_flags) | set(current_global_flags)
            if name in registered_flag_names() and previous_global_flags.get(name) != current_global_flags.get(name)
        ),
        project_flags=frozenset(
            name
            for name in set(previous_project_flags) | set(current_project_flags)
            if previous_project_flags.get(name) != current_project_flags.get(name)
        ),
        categories=frozenset(
            name
            for name in set(previous_categories) | set(current_categories)
            if previous_categories.get(name) != current_categories.get(name)
        ),
        collections=frozenset(
            name
            for name in set(previous_collections) | set(current_collections)
            if previous_collections.get(name) != current_collections.get(name)
        ),
        resolved_flags=frozenset(
            name
            for name in set(previous_resolved) | set(current_resolved)
            if previous_resolved.get(name) != current_resolved.get(name)
        ),
    )
    return ConfigurationUpdate(
        revision=delta.revision,
        identity=identity,
        previous_project=previous_project,
        current_project=current_project,
        previous_resolved_flags=previous_resolved,
        current_resolved_flags=current_resolved,
        changes=changes,
    )
