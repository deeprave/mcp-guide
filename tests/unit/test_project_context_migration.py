"""Focused unit coverage for Section 4 project-context migration."""

import asyncio
import os
import pwd
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from tests.helpers import create_test_runtime, request_context_for

from mcp_guide.filesystem.tools import send_directory_listing
from mcp_guide.models import Category
from mcp_guide.runtime import GuideRuntime, OwnerKey
from mcp_guide.session import Session
from mcp_guide.tools.tool_category import CategoryAddArgs, internal_category_add
from mcp_guide.tools.tool_project import SetCurrentProjectArgs, SwitchProjectArgs, internal_switch_project
from mcp_guide.validation import InvalidProjectNameError


def runtime_for_config(config_dir: str | Path) -> GuideRuntime[Session]:
    """Create an isolated runtime that owns configuration for ``config_dir``."""
    return create_test_runtime(str(config_dir))


@pytest.mark.anyio
async def test_binding_is_initial_only_and_name_switches_keep_root(tmp_path: Path) -> None:
    """Initial binding is immutable while name-only switching keeps its root."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("root-project"))
    root = "/client/workspace/root-project"

    await session.bind_project_path(root)
    initial_identity = session.active_configuration_identity
    session = await session.switch_project("review")

    assert session.bound_root_path == Path(root)
    assert session.project_name == "review"
    assert session.active_configuration_identity is not None
    assert session.active_configuration_identity[1] == initial_identity[1]

    with pytest.raises(ValueError, match="already bound"):
        await session.bind_project_path("/client/workspace/other-project")

    await session.cleanup()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("path", "expected_root"),
    [
        ("file:///client/workspace/uri-project", Path("/client/workspace/uri-project")),
        ("file:///client/workspace/uri%2Dencoded", Path("/client/workspace/uri-encoded")),
        ("FILE:///client/workspace/case-variant", Path("/client/workspace/case-variant")),
        ("file://LOCALHOST/client/workspace/local-host", Path("/client/workspace/local-host")),
    ],
)
async def test_binding_accepts_percent_encoded_local_file_uris(tmp_path: Path, path: str, expected_root: Path) -> None:
    """Initial binding decodes a local file URI without resolving client paths."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("file-uri-root"))

    await session.bind_project_path(path)

    assert session.bound_root_path == expected_root
    assert session.project_name == expected_root.name
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_requires_a_name_or_path_at_the_session_boundary(tmp_path: Path) -> None:
    """Direct Session callers cannot bypass the public selection requirement."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("missing-switch-selection"))
    await session.bind_project_path("/client/workspace/current")

    with pytest.raises(InvalidProjectNameError, match="requires a name or path"):
        await session.switch_project()

    assert session.bound_root_path == Path("/client/workspace/current")
    await session.cleanup()


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["", "   "])
async def test_switch_project_rejects_blank_path_selectors(tmp_path: Path, path: str) -> None:
    """Blank paths are not valid root-rebinding selectors."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("blank-switch-path"))
    await session.bind_project_path("/client/workspace/current")

    with pytest.raises(ValueError, match="requires a name or path"):
        SwitchProjectArgs(path=path)
    with pytest.raises(InvalidProjectNameError, match="requires a name or path"):
        await session.switch_project(path=path)

    await session.cleanup()


@pytest.mark.anyio
async def test_mutating_tool_does_not_update_a_project_rebound_mid_request(tmp_path: Path, monkeypatch) -> None:
    """A request resolved for an old root cannot persist into its replacement."""
    from anyio import Path as AsyncPath

    import mcp_guide.tools.tool_category as tool_category

    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("fenced-category-mutation"))
    await session.bind_project_path("/client/one/old")
    request_context = await request_context_for(session)
    mkdir_started = asyncio.Event()
    release_mkdir = asyncio.Event()

    class PausedPath:
        def __init__(self, path: str | Path) -> None:
            self._path = AsyncPath(path)

        async def mkdir(self, *args, **kwargs) -> None:
            mkdir_started.set()
            await release_mkdir.wait()
            await self._path.mkdir(*args, **kwargs)

    monkeypatch.setattr(tool_category, "AsyncPath", PausedPath)
    adding = asyncio.create_task(internal_category_add(CategoryAddArgs(name="leaked"), request_context))
    await mkdir_started.wait()
    replacement = await session.switch_project(path="/client/two/new")
    release_mkdir.set()

    result = await adding
    assert result.success is True
    assert "leaked" in (await session.get_project()).categories
    assert "leaked" not in (await replacement.get_project()).categories
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_rebinds_a_relative_root_with_the_same_public_id(tmp_path: Path, monkeypatch) -> None:
    """A relative root is normalised from the current root without filesystem lookup."""
    from mcp_guide.lazy_path import LazyPath

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("relative-root"))
    original = session

    await session.bind_project_path("/client/workspace/current")
    session = await session.switch_project(path="../wybra-dev")

    assert session.session_id == original.session_id
    assert session is not original
    assert session.bound_root_path == Path("/client/workspace/wybra-dev")
    assert session.project_name == "wybra-dev"
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_rebinds_to_an_expanded_home_root(tmp_path: Path, monkeypatch) -> None:
    """A root switch expands a user anchor and derives its configuration name."""
    from mcp_guide.lazy_path import LazyPath

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("user-anchored-switch"))

    await session.bind_project_path("/client/workspace/current")
    session = await session.switch_project(path="~/Code/wybra-dev")

    assert session.bound_root_path == home / "Code" / "wybra-dev"
    assert session.project_name == "wybra-dev"
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_rebinds_to_a_specific_user_home(tmp_path: Path, monkeypatch) -> None:
    """A root switch expands an explicit current-user anchor lexically."""
    from mcp_guide.lazy_path import LazyPath

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("specific-user-root-switch"))
    current_user = pwd.getpwuid(os.getuid())

    await session.bind_project_path("/client/workspace/current")
    session = await session.switch_project(path=f"~{current_user.pw_name}/Code/wybra-dev")

    assert session.bound_root_path == Path(current_user.pw_dir) / "Code" / "wybra-dev"
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_rejects_an_unknown_user_anchor(tmp_path: Path, monkeypatch) -> None:
    """An unknown user anchor returns the standard invalid-name result."""
    from mcp_guide.lazy_path import LazyPath

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("unknown-user-root-switch"))
    await session.bind_project_path("/client/workspace/current")

    result = await internal_switch_project(
        SwitchProjectArgs(path="~this-user-does-not-exist/Code/project"), await request_context_for(session)
    )

    assert result.success is False
    assert result.error_type == "invalid_name"
    assert "unknown user" in result.error
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_keeps_same_name_configurations_distinct_by_root(tmp_path: Path) -> None:
    """Same-name root rebinding refreshes identity, templates, and resolved flags."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("same-name-root-switch"))

    await session.bind_project_path("/client/one/shared")
    first_identity = session.active_configuration_identity
    template_cache = session.template_cache
    template_cache._cache = object()  # type: ignore[assignment]
    session.add_listener(session.task_manager)
    session.task_manager._resolved_flags = {"workflow": True}
    session = await session.switch_project(path="/client/two/shared")

    assert session.project_name == "shared"
    assert session.active_configuration_identity is not None
    assert session.active_configuration_identity != first_identity
    assert session.template_cache is not template_cache
    assert session.task_manager._resolved_flags != {"workflow": True}
    directory_result = await send_directory_listing(session, "docs", [])
    assert directory_result.success is True
    old_root_result = await send_directory_listing(session, "/client/one/shared/docs", [])
    assert old_root_result.success is False
    await session.cleanup()


@pytest.mark.anyio
async def test_initial_bind_listener_can_publish_a_configuration_mutation(tmp_path: Path) -> None:
    """Initial binding runs listeners in the task that owns the transition gate."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("initial-bind-listener-mutation"))

    class Listener:
        async def on_project_changed(self, observed: Session, old_project: str, new_project: str) -> None:
            await observed.update_config(
                lambda project: project.with_category("docs", Category(dir="docs/", patterns=[]))
            )

        async def on_config_changed(self, observed: Session) -> None:
            pass

    session.add_listener(Listener())
    await asyncio.wait_for(session.bind_project_path("/client/one/shared"), timeout=1)

    assert "docs" in (await session.get_project()).categories
    await session.cleanup()


@pytest.mark.anyio
async def test_switch_project_reports_root_rebinding(tmp_path: Path) -> None:
    """A path switch reports its root-rebinding behaviour to callers."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("root-switch-result"))
    await session.bind_project_path("/client/workspace/current")

    result = await internal_switch_project(
        SwitchProjectArgs(path="/client/workspace/wybra-dev"), await request_context_for(session)
    )

    assert result.success is True
    assert result.message == "Rebound project root and selected configuration project 'wybra-dev'"
    await session.cleanup()


@pytest.mark.anyio
async def test_binding_user_anchored_root_expands_before_storing(tmp_path: Path, monkeypatch) -> None:
    """A bound root stores the expanded absolute client path."""
    from mcp_guide.lazy_path import LazyPath

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
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
    """Concurrent initial preparations cannot overwrite a successful binding."""
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


def test_project_selection_schemas_separate_root_path_from_configuration_name() -> None:
    """The public schemas advertise independent switch name and path fields."""
    set_schema = SetCurrentProjectArgs.model_json_schema()
    switch_schema = SwitchProjectArgs.model_json_schema()

    assert set_schema["required"] == ["path"]
    assert "name" not in set_schema["properties"]
    assert "name" not in switch_schema.get("required", [])
    assert "path" not in switch_schema.get("required", [])
    validator = Draft202012Validator(switch_schema)
    assert validator.is_valid({"name": "review"})
    assert validator.is_valid({"name": "review", "path": None})
    assert validator.is_valid({"path": "../other-project"})
    assert validator.is_valid({"name": None, "path": "../other-project"})
    assert not validator.is_valid({})
    assert not validator.is_valid({"name": None})
    assert not validator.is_valid({"name": "review", "path": "../other-project"})
    assert (
        switch_schema["properties"]["name"]["description"] == "Configuration project name to select at the current root"
    )
    assert "Project root to rebind" in switch_schema["properties"]["path"]["description"]
    assert "verified stdio filesystem sharing" in switch_schema["properties"]["path"]["description"]
