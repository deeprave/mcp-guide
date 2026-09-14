"""Behaviour tests for configuration snapshot and session update contracts."""

from mcp_guide.configuration_update import ConfigurationSnapshotDelta, ProjectIdentity, derive_configuration_update
from mcp_guide.utils.project_hash import generate_project_key


def test_snapshot_delta_identifies_global_and_strict_project_changes() -> None:
    """A snapshot delta exposes only configuration-layer change selection data."""
    delta = ConfigurationSnapshotDelta(
        revision=4,
        previous={"feature_flags": {"command": False}, "projects": {}},
        current={"feature_flags": {"command": True}, "projects": {}},
        changed_project_identities=frozenset({ProjectIdentity("guide", "abc123")}),
    )

    assert delta.revision == 4
    assert delta.global_flags_changed
    assert delta.changed_project_identities == frozenset({ProjectIdentity("guide", "abc123")})


def test_effective_update_ignores_an_unknown_global_flag() -> None:
    """Only registered flags are projected to session consumers."""
    identity = ProjectIdentity("guide", "abc123")
    delta = ConfigurationSnapshotDelta(
        revision=1,
        previous={"feature_flags": {"unregistered": False}, "projects": {}},
        current={"feature_flags": {"unregistered": True}, "projects": {}},
        changed_project_identities=frozenset(),
    )

    assert derive_configuration_update(delta, identity).changes.is_empty


def test_effective_update_preserves_project_categories_and_masks_global_overrides() -> None:
    """Projection preserves an immutable project view and omits an ineffective global change."""
    identity = ProjectIdentity("guide", "abc123")
    key = generate_project_key(identity.name, identity.root_hash)
    project = {
        "name": "guide",
        "hash": "abc123",
        "categories": {"docs": {"dir": "docs", "patterns": ["*.md"]}},
        "project_flags": {"workflow": True},
    }
    delta = ConfigurationSnapshotDelta(
        revision=1,
        previous={"feature_flags": {"workflow": False}, "projects": {key: project}},
        current={"feature_flags": {"workflow": True}, "projects": {key: project}},
        changed_project_identities=frozenset(),
    )

    update = derive_configuration_update(delta, identity)

    assert update.changes.global_flags == frozenset({"workflow"})
    assert update.changes.resolved_flags == frozenset()
    assert update.changes.is_empty
    assert update.current_project is not None
    assert update.current_project["categories"]["docs"]["dir"] == "docs"


def test_effective_update_reports_removal_of_an_empty_active_project() -> None:
    """A removed project must still reach its bound Session for invalidation."""
    identity = ProjectIdentity("guide", "abc123")
    key = generate_project_key(identity.name, identity.root_hash)
    project = {"name": "guide", "hash": "abc123"}
    delta = ConfigurationSnapshotDelta(
        revision=1,
        previous={"feature_flags": {}, "projects": {key: project}},
        current={"feature_flags": {}, "projects": {}},
        changed_project_identities=frozenset({identity}),
    )

    update = derive_configuration_update(delta, identity)

    assert update.previous_project is not None
    assert update.current_project is None
    assert not update.changes.is_empty
