"""Command discovery reads real files, metadata, requirements and session-local caches."""

import asyncio
from pathlib import Path

import pytest
import yaml

from mcp_guide.discovery.commands import discover_commands
from tests.helpers import create_bound_test_session


@pytest.fixture
async def command_session(runtime, tmp_path):
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    return await create_bound_test_session(runtime, "commands")


@pytest.mark.anyio
async def test_discovery_metadata_aliases_and_nested_commands(command_session, tmp_path, caplog):
    commands = tmp_path / "_commands"
    nested = commands / "create"
    nested.mkdir(parents=True)
    (nested / "category.mustache").write_text("Create category")
    (commands / "simple.md").write_text("Simple command")
    (commands / "help.md").write_text(
        "---\ndescription: Show commands\nusage: ':help [command]'\n"
        "examples: [':help', ':help create/category']\n"
        "aliases: [h, '?', '?foo=bar', project/perm, ../escape, 'project?verbose', "
        "'project/table?table=true', 'project/topic?label=a?b']\n---\nHelp"
    )
    found = {item["name"]: item for item in await discover_commands(commands, command_session)}
    assert set(found) == {"create/category", "simple", "help"}
    assert found["simple"] == {
        "name": "simple",
        "path": str(commands / "simple.md"),
        "description": "",
        "usage": "",
        "examples": [],
        "aliases": [],
        "alias_metadata": [],
        "category": "general",
    }
    help_command = found["help"]
    assert help_command["description"] == "Show commands"
    assert help_command["usage"] == ":help [command]"
    assert help_command["examples"] == [":help", ":help create/category"]
    assert help_command["aliases"] == [
        "h",
        "project/perm",
        "project?verbose",
        "project/table?table=true",
        "project/topic?label=a?b",
    ]
    assert help_command["alias_metadata"] == [
        {"raw": "h", "path": "h", "implied_kwargs": {}},
        {"raw": "project/perm", "path": "project/perm", "implied_kwargs": {}},
        {"raw": "project?verbose", "path": "project", "implied_kwargs": {"verbose": True}},
        {"raw": "project/table?table=true", "path": "project/table", "implied_kwargs": {"table": True}},
        {"raw": "project/topic?label=a?b", "path": "project/topic", "implied_kwargs": {"label": "a?b"}},
    ]
    for invalid in ("?", "?foo=bar", "../escape"):
        assert repr(invalid) in caplog.text


@pytest.mark.anyio
async def test_requirements_follow_real_workflow_enablement(command_session, tmp_path):
    commands = tmp_path / "_commands"
    commands.mkdir()
    (commands / "plan.md").write_text("---\nrequires-workflow: [planning]\n---\nPlan")
    (commands / "workflow.md").write_text("---\nrequires-workflow: true\n---\nWorkflow")
    (commands / "feature.md").write_text("---\nrequires-feature: enabled\n---\nFeature")
    assert await discover_commands(commands, command_session) == []
    await command_session.project_flags().set("workflow", True)
    assert {item["name"] for item in await discover_commands(commands, command_session)} == {"plan", "workflow"}


@pytest.mark.anyio
async def test_general_phase_guidance_remains_available_without_workflow(command_session):
    commands = Path("src/mcp_guide/templates/_commands").resolve()
    names = {item["name"] for item in await discover_commands(commands, command_session)}
    assert {f"workflow/{name}" for name in ("discuss", "explore", "plan", "implement", "check", "review")} <= names
    assert not {f"workflow/{name}" for name in ("show", "issue", "reset", "phase")} & names


@pytest.mark.anyio
async def test_cache_is_session_local_and_development_mode_refreshes_files(command_session, runtime, tmp_path):
    commands = tmp_path / "_commands"
    commands.mkdir()
    (commands / "first.md").write_text("First")
    original = await discover_commands(commands, command_session)
    assert [item["name"] for item in original] == ["first"]
    (commands / "second.md").write_text("Second")
    assert await discover_commands(commands, command_session) == original
    second_session = await create_bound_test_session(runtime, "second")
    assert {item["name"] for item in await discover_commands(commands, second_session)} == {"first", "second"}
    assert await discover_commands(commands, command_session) == original
    await runtime.feature_flags().set("guide-development", True)
    assert {item["name"] for item in await discover_commands(commands, command_session)} == {"first", "second"}


@pytest.mark.anyio
async def test_unreadable_file_is_skipped_and_does_not_poison_cache(command_session, tmp_path, caplog):
    commands = tmp_path / "_commands"
    commands.mkdir()
    broken = commands / "broken.md"
    broken.write_bytes(bytes([255]))
    (commands / "valid.md").write_text("Valid")
    assert [item["name"] for item in await discover_commands(commands, command_session)] == ["valid"]
    assert command_session.task_manager.command_cache == {}
    assert "Failed to parse 1 command files" in caplog.text
    broken.write_text("Repaired")
    assert {item["name"] for item in await discover_commands(commands, command_session)} == {"broken", "valid"}


@pytest.mark.anyio
async def test_development_stat_failure_still_discovers_commands(command_session, runtime, tmp_path, monkeypatch):
    commands = tmp_path / "_commands"
    commands.mkdir()
    (commands / "test.md").write_text("Test")
    await runtime.feature_flags().set("guide-development", True)
    to_thread = asyncio.to_thread
    stat_attempts = []

    async def fail_directory_stat(function, *args, **kwargs):
        if function.__name__ == "_max_file_mtime":
            stat_attempts.append(True)
            raise OSError("stat failed")
        return await to_thread(function, *args, **kwargs)

    # Deterministic OS stat failure; file discovery and parsing still use the real filesystem.
    monkeypatch.setattr("mcp_guide.discovery.commands.asyncio.to_thread", fail_directory_stat)
    assert [item["name"] for item in await discover_commands(commands, command_session)] == ["test"]
    assert stat_attempts == [True]
