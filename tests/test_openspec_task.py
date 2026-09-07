"""OpenSpec detection, persistence and response handling through real session state."""

import json

import pytest
import yaml

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.openspec.state import parse_openspec_state
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType
from tests.helpers import bind_isolated_test_session


@pytest.fixture
async def openspec_session(runtime, tmp_path):
    docs = tmp_path / "docs"
    templates = docs / "_openspec"
    templates.mkdir(parents=True)
    for name, body in {
        "openspec-cli-check": "Locate CLI",
        "openspec-version-check": "Read version",
        "openspec-project-check": "Check project",
        "openspec-get-changes": "Read changes",
        "_status-format": "{{changeName}} {{#isComplete}}complete{{/isComplete}}{{^isComplete}}pending{{/isComplete}}",
        "_show-format": "{{changeName}}: {{description}}",
        "_error-format": "{{error}}: {{message}}",
        "_list-format": "Current changes",
    }.items():
        (templates / f"{name}.mustache").write_text(body)
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docs), "projects": {}}))
    session = await bind_isolated_test_session(runtime)
    await session.project_flags().set("openspec", FeatureValue(True))
    return session


@pytest.mark.anyio
@pytest.mark.parametrize("age", [None, 100, 86400], ids=["absent", "recent", "expired"])
async def test_initialisation_reuses_only_recent_global_state(openspec_session, runtime, monkeypatch, age):
    now = 100000.0
    monkeypatch.setattr("time.time", lambda: now)
    if age is not None:
        await runtime.feature_flags().set(
            "openspec-state", FeatureValue({"validated": "true", "version": "1.10.0", "checked": str(now - age)})
        )
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    assert task.is_available() is None
    assert task.get_version() is None
    assert task.get_changes() is None
    assert (await task.handle_event(EventType.TIMER_ONCE, {})).result
    instruction = (await manager.process_result(Result.ok())).additional_agent_instructions
    assert instruction == ("Check project" if age == 100 else "Locate CLI")
    if age == 100:
        assert task.is_available() is True
        assert task.get_version() == "1.10.0"
    await task.on_tool()
    assert manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "content,version", [("openspec version 1.10.2", "1.10.2"), ("v2.0.1", "2.0.1"), ("invalid", None)]
)
async def test_version_response_persists_and_controls_project_check(
    openspec_session, runtime, monkeypatch, content, version
):
    monkeypatch.setattr("time.time", lambda: 1000.0)
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    assert not task.meets_minimum_version("1.0.0")
    result = await task.handle_event(EventType.FS_FILE_CONTENT, {"path": ".openspec-version.txt", "content": content})
    assert result.result
    assert task.get_version() == version
    assert manager.get_cached_data("openspec_version") == version
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.version == version
    assert state.validated is (version is not None)
    assert state.checked == 1000.0
    instruction = (await manager.process_result(Result.ok())).additional_agent_instructions
    assert instruction == ("Check project" if version else None)
    if version == "1.10.2":
        assert task.meets_minimum_version("v1.9.6")
        assert task.meets_minimum_version("1.10.2")
        assert not task.meets_minimum_version("1.10.3")
        assert not task.meets_minimum_version("2.0.0")


@pytest.mark.anyio
async def test_missing_cli_persists_unavailability_without_followup(openspec_session, runtime):
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    result = await task.handle_event(EventType.FS_COMMAND, {"command": "openspec", "found": False})
    assert result.result
    assert task.is_available() is False
    assert manager.is_queue_empty()
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.validated is False
    assert state.version is None
    assert state.checked is not None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "name,data,expected,success",
    [
        ("status", {"changeName": "demo", "isComplete": True}, "demo complete", True),
        ("status", {"changeName": "demo", "isComplete": False}, "demo pending", True),
        ("show", {"changeName": "demo", "description": "Description"}, "demo: Description", True),
        ("status", {"error": "Missing option", "message": "Specify change"}, "Missing option: Specify change", False),
    ],
    ids=["complete", "pending", "show", "error"],
)
async def test_response_rendering_and_cache(openspec_session, name, data, expected, success):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    result = await task.handle_event(
        EventType.FS_FILE_CONTENT, {"path": f".openspec-{name}.json", "content": json.dumps(data)}
    )
    assert result.result is success
    assert result.rendered_content.content == expected
    if success:
        assert (task.get_status() if name == "status" else task.get_show()) == data
    else:
        assert task.get_status() is None


@pytest.mark.anyio
@pytest.mark.parametrize("empty", [False, True], ids=["grouped", "empty"])
async def test_changes_grouping_and_timer_expiry(openspec_session, monkeypatch, empty):
    now = 1000.0
    monkeypatch.setattr("time.time", lambda: now)
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    changes = (
        []
        if empty
        else [
            {
                "name": "active",
                "status": "in-progress",
                "completedTasks": 2,
                "totalTasks": 5,
                "lastModified": "invalid",
            },
            {"name": "draft", "status": "no-tasks", "totalTasks": 0},
            {"name": "done", "status": "complete", "completedTasks": 5, "totalTasks": 5},
        ]
    )
    result = await task.handle_event(
        EventType.FS_FILE_CONTENT, {"path": ".openspec-changes.json", "content": json.dumps({"changes": changes})}
    )
    assert result.rendered_content.content == "Current changes"
    assert openspec_session.task_manager.get_cached_data("openspec_changes") == changes
    grouped = task.get_changes()
    if empty:
        assert grouped == {"in_progress": [], "draft": [], "complete": []}
    else:
        assert grouped["in_progress"][0]["progress"] == "2/5"
        assert grouped["in_progress"][0]["humanized_date"] == "invalid"
        assert grouped["draft"][0]["progress"] == "N/A"
        assert grouped["complete"][0]["name"] == "done"
    now += 100
    assert (await task.handle_event(EventType.TIMER, {"interval": 3600.0})).result
    assert task.get_changes() == grouped
    now += 3600
    assert (await task.handle_event(EventType.TIMER, {"interval": 3600.0})).result
    assert task.get_changes() is None
    assert not task.is_cache_valid()


@pytest.mark.anyio
async def test_unrelated_or_malformed_responses_are_ignored(openspec_session):
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    for path, content in [("other.md", "Text"), (".openspec-status.json", "not JSON"), ("other.json", "{}")]:
        assert await task.handle_event(EventType.FS_FILE_CONTENT, {"path": path, "content": content}) is None
    assert manager.is_queue_empty()
    assert task.get_status() is None
    assert task.get_show() is None
