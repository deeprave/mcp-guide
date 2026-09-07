"""Project tools operate on real bindings and persisted configuration."""

from dataclasses import replace

import pytest
import yaml
from tests.helpers import create_test_session, create_unbound_test_session, request_context_for

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import Category, Collection, Project
from mcp_guide.models.project import ExportedTo
from mcp_guide.tools.tool_project import (
    CloneProjectArgs,
    GetCurrentProjectArgs,
    ListProjectArgs,
    ListProjectsArgs,
    SetCurrentProjectArgs,
    internal_clone_project,
    internal_get_project,
    internal_list_project,
    internal_list_projects,
    internal_set_project,
)
from mcp_guide.validation import InvalidProjectNameError


@pytest.fixture(autouse=True)
def minimal_configuration(runtime, tmp_path):
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(tmp_path / "docs"), "projects": {}})
    )


@pytest.mark.anyio
async def test_unbound_project_tools_return_guidance(runtime):
    context = await request_context_for(create_unbound_test_session(runtime))
    for handler, args in [
        (internal_get_project, GetCurrentProjectArgs()),
        (internal_clone_project, CloneProjectArgs(from_project="source")),
    ]:
        result = await handler(args, context)
        assert not result.success
        assert result.error_type == "no_project"
        assert result.instruction


@pytest.mark.anyio
@pytest.mark.parametrize("verbose,has_data", [(False, True), (True, True), (False, False)])
async def test_bind_and_get_project_output_excludes_global_flags(runtime, tmp_path, verbose, has_data):
    source = await create_test_session(runtime, "target")
    if has_data:
        await source.update_config(
            lambda p: replace(
                p,
                categories={"python": Category(dir="src", patterns=["*.py"], description="Python")},
                collections={"backend": Collection(categories=["python"], description="Backend")},
                project_flags={"debug": FeatureValue(True), "env": FeatureValue("test")},
            )
        )
    await runtime.feature_flags().set("global-only", FeatureValue(True))
    session = create_unbound_test_session(runtime)
    context = await request_context_for(session)
    bound = await internal_set_project(
        SetCurrentProjectArgs(path=str(source.bound_root_path), verbose=verbose), context
    )
    assert bound.success
    assert bound.message == "Bound project root for 'target'"
    current = await internal_get_project(GetCurrentProjectArgs(verbose=verbose), await request_context_for(session))
    assert current.success
    assert current.value == bound.value
    assert current.value["project"] == "target"
    if not has_data:
        assert current.value["categories"] == []
        assert current.value["collections"] == []
        assert current.value["flags"] == []
    elif verbose:
        assert current.value["categories"] == [
            {"name": "python", "dir": "src/", "patterns": ["*.py"], "description": "Python"}
        ]
        assert current.value["collections"] == [{"name": "backend", "categories": ["python"], "description": "Backend"}]
        assert current.value["flags"] == {"debug": True, "env": "test"}
    else:
        assert current.value["categories"] == ["python"]
        assert current.value["collections"] == ["backend"]
        assert set(current.value["flags"]) == {"debug", "env"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "error,error_type",
    [
        (InvalidProjectNameError("Invalid project"), "invalid_name"),
        (ValueError("Invalid path"), "project_error"),
        (RuntimeError("Configuration unavailable"), "project_load_error"),
    ],
)
async def test_binding_error_mapping(runtime, monkeypatch, error, error_type):
    # Inject failure at binding to cover the tool's distinct error mappings.
    async def fail_binding(*args):
        raise error

    monkeypatch.setattr("mcp_guide.tools.tool_project.bind_session_project", fail_binding)
    context = await request_context_for(create_unbound_test_session(runtime))
    result = await internal_set_project(SetCurrentProjectArgs(path="/client/project"), context)
    assert not result.success
    assert result.error_type == error_type
    assert result.error == str(error)


@pytest.mark.anyio
async def test_listing_current_named_and_exact_projects_without_switching(runtime):
    current = await create_test_session(runtime, "current")
    other = await create_test_session(runtime, "other")
    await other.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    context = await request_context_for(current)
    listed = await internal_list_projects(ListProjectsArgs(), context)
    assert listed.value == {"projects": ["current", "other"]}
    verbose = await internal_list_projects(ListProjectsArgs(verbose=True), context)
    assert set(verbose.value["projects"]) == {current.project.key, other.project.key}
    assert verbose.value["projects"][other.project.key]["categories"][0]["name"] == "docs"
    for name, expected in [(None, "current"), ("other", "other"), (other.project.key, "other")]:
        result = await internal_list_project(ListProjectArgs(name=name, verbose=True), context)
        assert result.success
        assert result.value["project"] == expected
    missing = await internal_list_project(ListProjectArgs(name="missing"), context)
    assert not missing.success
    assert "not found" in missing.error
    assert current.project.name == "current"


@pytest.mark.anyio
@pytest.mark.parametrize("merge", [True, False], ids=["merge", "replace"])
async def test_clone_persists_transferable_settings_and_retains_identity(runtime, merge):
    source = await create_test_session(runtime, "source")
    target = await create_test_session(runtime, "target")
    for session, own in [(source, "source"), (target, "target")]:
        await session.update_config(
            lambda p, own=own: replace(
                p,
                categories={"shared": Category(dir=own, patterns=["*.md"]), own: Category(dir=own, patterns=["*.txt"])},
                collections={
                    "shared": Collection(categories=["shared"], description=own),
                    own: Collection(categories=[own]),
                },
                project_flags={"shared": FeatureValue(own), own: FeatureValue(True)},
                allowed_write_paths=[f"{own}/"],
                additional_read_paths=[f"/Users/{own}/read"],
                exports={("docs", None): ExportedTo(path=f"{own}.md", metadata_hash=own)},
            )
        )
    identity = (target.project.name, target.project.key, target.project.hash)
    context = await request_context_for(target)
    if not merge:
        refused = await internal_clone_project(CloneProjectArgs(from_project="source", merge=False), context)
        assert refused.error_type == "safeguard_prevented"
    result = await internal_clone_project(
        CloneProjectArgs(from_project=source.project.key, merge=merge, force=True), context
    )
    assert result.success
    assert result.value["to_project"] == "target"
    for kind in ("categories", "collections"):
        assert result.value[f"{kind}_added"] == (1 if merge else 2)
        assert result.value[f"{kind}_overwritten"] == (1 if merge else 0)
    assert bool(result.value["warnings"]) is merge
    cloned = await target.get_project()
    assert (cloned.name, cloned.key, cloned.hash) == identity
    assert set(cloned.categories) == ({"shared", "source", "target"} if merge else {"shared", "source"})
    assert set(cloned.collections) == set(cloned.categories)
    assert cloned.collections["shared"].description == "source"
    assert cloned.project_flags == (
        {"shared": "source", "source": True, "target": True} if merge else {"shared": "source", "source": True}
    )
    assert cloned.allowed_write_paths == ["source/"]
    assert cloned.additional_read_paths == ["/Users/source/read"]
    assert cloned.exports[("docs", None)].path == "source.md"


@pytest.mark.anyio
async def test_clone_recovers_explicit_hashless_legacy_source(runtime):
    """Clone can recover a deliberately named pre-hash YAML entry."""
    target = await create_test_session(runtime, "target")

    config_manager = target._config()
    config = yaml.safe_load(config_manager.config_file.read_text())
    config["projects"]["source"] = {"categories": {"docs": {"dir": "docs", "patterns": ["*.md"]}}}
    config_manager.config_file.write_text(yaml.safe_dump(config))
    await config_manager._on_external_change(str(config_manager.config_file))

    result = await internal_clone_project(
        CloneProjectArgs(from_project="source", merge=False, force=True), await request_context_for(target)
    )

    assert result.success
    assert result.value["from_project"] == "source"
    assert result.value["categories_added"] == 1


@pytest.mark.anyio
async def test_clone_rejects_invalid_missing_sources_and_reports_write_failure(runtime, monkeypatch):
    source = await create_test_session(runtime, "source")
    target = await create_test_session(runtime, "target")
    context = await request_context_for(target)
    for name, error in [("../etc", "invalid_name"), ("missing", "not_found")]:
        result = await internal_clone_project(CloneProjectArgs(from_project=name), context)
        assert not result.success
        assert result.error_type == error

    # Deterministic failed persistence; OS permission behaviour varies by runner.
    async def fail_save(project):
        raise OSError("config write failed")

    monkeypatch.setattr(target, "save_project", fail_save)
    result = await internal_clone_project(CloneProjectArgs(from_project=source.project.key), context)
    assert not result.success
    assert result.error_type == "config_write_error"


@pytest.mark.anyio
async def test_clone_safeguard_uses_reloaded_dirty_project(runtime):
    target = await create_test_session(runtime, "target")
    await target.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    await create_test_session(runtime, "source")
    current = target.project
    # Simulate a stale in-memory snapshot while retaining real persisted data.
    target._Session__delegate.bind(Project(name=current.name, key=current.key, hash=current.hash))
    target._project_dirty = True
    result = await internal_clone_project(
        CloneProjectArgs(from_project="source", merge=False), await request_context_for(target)
    )
    assert not result.success
    assert result.error_type == "safeguard_prevented"
