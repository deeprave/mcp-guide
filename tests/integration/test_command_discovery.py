"""Command discovery parses isolated files, metadata, requirements and caches."""

import pytest
import yaml

from mcp_guide.discovery.commands import discover_commands
from tests.helpers import create_bound_test_session


@pytest.fixture
async def command_session(runtime, tmp_path):
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    return await create_bound_test_session(runtime, "commands")


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
    stat_attempts = []

    def fail_directory_scan(self, *args, **kwargs):
        stat_attempts.append(True)
        raise OSError("stat failed")

    # Deterministic OS stat failure during the dev-mode mtime scan; file
    # discovery and parsing still use the real filesystem.
    monkeypatch.setattr("mcp_guide.discovery.commands.AsyncPath.rglob", fail_directory_scan)
    assert [item["name"] for item in await discover_commands(commands, command_session)] == ["test"]
    assert stat_attempts == [True]
