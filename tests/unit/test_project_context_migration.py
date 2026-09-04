"""Focused unit coverage for Section 4 project-context migration."""

import asyncio
from pathlib import Path

import pytest
from tests.helpers import create_test_runtime

from mcp_guide.runtime import GuideRuntime, OwnerKey
from mcp_guide.session import Session
from mcp_guide.tools.tool_project import SetCurrentProjectArgs, SwitchProjectArgs


def runtime_for_config(config_dir: str | Path) -> GuideRuntime[Session]:
    """Create an isolated runtime that owns configuration for ``config_dir``."""
    return create_test_runtime(str(config_dir))


@pytest.mark.anyio
async def test_binding_is_path_based_immutable_and_configuration_switches_keep_root(tmp_path: Path) -> None:
    """Root binding happens once; configuration selection is independent."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("root-project"))
    root = "/client/workspace/root-project"

    await session.bind_project_path(root)
    initial_identity = session.active_configuration_identity
    await session.switch_project("review")

    assert session.bound_root_path == Path(root)
    assert session.project_name == "review"
    assert session.active_configuration_identity is not None
    assert session.active_configuration_identity[1] == initial_identity[1]

    with pytest.raises(ValueError, match="already bound"):
        await session.bind_project_path("/client/workspace/other-project")

    with pytest.raises(ValueError, match="configuration name, not a filesystem path"):
        await session.switch_project("/client/workspace/other-project")

    await session.cleanup()


@pytest.mark.anyio
async def test_binding_user_anchored_root_expands_before_storing(tmp_path: Path, monkeypatch) -> None:
    """A bound root stores the expanded absolute client path."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("user-anchored-root"))

    await session.bind_project_path("~/project")

    assert session.bound_root_path == home / "project"
    await session.cleanup()


@pytest.mark.anyio
async def test_same_configuration_name_at_distinct_roots_has_independent_strict_keys(tmp_path: Path) -> None:
    """Hash-suffixed keys prevent name-only cross-root selection."""
    runtime = runtime_for_config(tmp_path)
    first = runtime.resolve_session(OwnerKey("first"))
    second = runtime.resolve_session(OwnerKey("second"))

    await first.bind_project_path("/client/one/shared")
    await second.bind_project_path("/client/two/shared")

    first_project = await first.get_project()
    second_project = await second.get_project()
    assert first_project.name == second_project.name == "shared"
    assert first_project.hash != second_project.hash
    assert first_project.key != second_project.key

    await first.cleanup()
    await second.cleanup()


@pytest.mark.anyio
async def test_mismatched_persisted_entry_is_ignored_and_correct_key_is_created(tmp_path: Path) -> None:
    """A familiar name cannot select an entry whose hash is for another root."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("strict-project"))
    root = Path("/client/workspace/strict-project")
    wrong_hash = "a" * 64
    manager = runtime.configuration_service()
    manager._ensure_config_dir()
    manager.config_file.write_text(f"projects:\n  strict-project-{wrong_hash[:8]}:\n    hash: {wrong_hash}\n")

    await session.bind_project_path(root)
    project = await session.get_project()

    assert project.hash != wrong_hash
    assert project.key != f"strict-project-{wrong_hash[:8]}"
    assert project.key in await session.get_all_projects()

    await session.cleanup()


@pytest.mark.anyio
async def test_project_writes_reject_a_key_that_does_not_match_its_hash(tmp_path: Path) -> None:
    """Configuration persistence cannot introduce a malformed project identity."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("project"))
    await session.bind_project_path("/client/workspace/project")
    project = await session.get_project()

    with pytest.raises(ValueError, match="must match"):
        await runtime.configuration_service().save_project_config("project-deadbeef", project)

    await session.cleanup()


@pytest.mark.anyio
async def test_concurrent_bind_project_path_rejects_the_second_root(tmp_path: Path) -> None:
    """A Session bind lock serialises root assignment; the loser sees an already-bound root."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("concurrent-bind"))

    async def bind(path: str) -> str:
        try:
            await session.bind_project_path(path)
            return "ok"
        except ValueError:
            return "bound"

    first, second = await asyncio.gather(
        bind("/client/one/alpha"),
        bind("/client/two/beta"),
    )

    assert {first, second} == {"ok", "bound"}
    assert session.bound_root_path in {Path("/client/one/alpha"), Path("/client/two/beta")}
    await session.cleanup()


@pytest.mark.anyio
async def test_bind_notifies_after_releasing_the_bind_lock(tmp_path: Path) -> None:
    """Project-change listeners must not run while the bind lock is held."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("notify-after-lock"))
    original_notify = session._notify_project_changed

    async def notify_outside_lock(old_project: str, new_project: str) -> None:
        assert not session._bind_lock.locked()
        await original_notify(old_project, new_project)

    session._notify_project_changed = notify_outside_lock  # type: ignore[method-assign]
    await session.bind_project_path("/client/workspace/notify-project")
    await session.cleanup()


def test_project_selection_schemas_separate_root_path_from_configuration_name() -> None:
    """The public models cannot regress to name-based root selection."""
    set_schema = SetCurrentProjectArgs.model_json_schema()
    switch_schema = SwitchProjectArgs.model_json_schema()

    assert set_schema["required"] == ["path"]
    assert "name" not in set_schema["properties"]
    assert switch_schema["required"] == ["name"]
    assert "path" not in switch_schema["properties"]
