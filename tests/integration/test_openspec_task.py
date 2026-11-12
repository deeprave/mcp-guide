"""OpenSpec detection, persistence and response handling through real session state."""

import json

import pytest
import yaml

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.openspec.state import parse_openspec_state
from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.prompts.guide_prompt import handle_command
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, TaskActivation
from tests.helpers import create_bound_test_session, request_context_for


@pytest.fixture
async def openspec_session(runtime, tmp_path):
    docs = tmp_path / "docs"
    templates = docs / "_openspec"
    templates.mkdir(parents=True)
    for name, body in {
        "openspec-check": "Detect OpenSpec",
        "_status-format": "{{changeName}} {{#isComplete}}complete{{/isComplete}}{{^isComplete}}pending{{/isComplete}}",
        "_show-format": "{{changeName}}: {{description}}",
        "_error-format": "{{error}}: {{message}}{{#init_advised}} init-advised{{/init_advised}}",
        "_list-format": "Current changes",
    }.items():
        (templates / f"{name}.mustache").write_text(body)
    command_dir = docs / "_commands" / "openspec"
    command_dir.mkdir(parents=True)
    (command_dir / "list.mustache").write_text(
        "{{#kwargs.force}}{{#openspec.refresh_changes}}{{openspec.changes_refresh_id}}{{/openspec.refresh_changes}}"
        "{{/kwargs.force}}{{^kwargs.force}}{{#openspec.request_changes}}{{openspec.changes_refresh_id}}"
        "{{/openspec.request_changes}}{{/kwargs.force}}"
    )
    (command_dir / "archive.mustache").write_text(
        "{{#openspec.invalidate_results}}{{/openspec.invalidate_results}}archive"
    )
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docs), "projects": {}}))
    session = await create_bound_test_session(runtime)
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
        await openspec_session.wait_for_configuration_updates()
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    assert task.is_available() is None
    assert task.get_version() is None
    assert task.get_changes() is None
    assert (await task.handle_event(EventType.TIMER_ONCE, {})).result
    instruction = (await manager.process_result(Result.ok())).additional_agent_instructions
    assert instruction == ("Detect OpenSpec" if age in {None, 86400} else None)
    if age == 100:
        assert task.is_available() is True
        assert task.get_version() == "1.10.0"
    await task.on_tool()
    assert manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "report,version",
    [
        ({"version": "openspec version 1.10.2"}, "1.10.2"),
        ({"version": "v2.0.1"}, "2.0.1"),
        ({"version": "invalid"}, None),
    ],
)
async def test_version_detection_response_persists_global_state(
    openspec_session, runtime, monkeypatch, report, version
):
    monkeypatch.setattr("time.time", lambda: 1000.0)
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    assert not task.meets_minimum_version("1.0.0")
    result = await task.handle_event(
        EventType.FS_FILE_CONTENT, {"path": ".openspec-info.json", "content": json.dumps(report)}
    )
    assert result.result
    # Persisting global state schedules a fresh project-task activation.  The
    # replacement is the authority for subsequent cache and instruction state.
    await openspec_session.wait_for_configuration_updates()
    task = manager.get_task_by_type(OpenSpecTask)
    assert task is not None
    assert (await task.handle_event(EventType.TIMER_ONCE, {})).result
    assert task.get_version() == version
    assert manager.get_cached_data("openspec_version") == version
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.version == version
    assert state.validated is (version is not None)
    assert state.checked == 1000.0
    assert (await manager.process_result(Result.ok())).additional_agent_instructions is None
    if version == "1.10.2":
        assert task.meets_minimum_version("v1.9.6")
        assert task.meets_minimum_version("1.10.2")
        assert not task.meets_minimum_version("1.10.3")
        assert not task.meets_minimum_version("2.0.0")


@pytest.mark.anyio
async def test_missing_cli_persists_unavailability_without_followup(openspec_session, runtime):
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    result = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-info.json", "content": json.dumps({"version": None})},
    )
    assert result.result
    assert task.is_available() is False
    assert manager.is_queue_empty()
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.validated is False
    assert state.version is None
    assert state.checked is not None


@pytest.mark.anyio
async def test_enable_transition_is_passive_about_project_store(openspec_session, runtime):
    manager = openspec_session.task_manager
    task = OpenSpecTask()
    activation = TaskActivation(manager, task, openspec_session, enabled_flags=frozenset({"openspec"}))
    assert await task.start(activation)

    assert (await task.handle_event(EventType.TIMER_ONCE, {})).result
    assert (await manager.process_result(Result.ok())).additional_agent_instructions == "Detect OpenSpec"
    detection = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-info.json", "content": json.dumps({"version": "1.2.3"})},
    )
    assert detection is not None and detection.result
    state = parse_openspec_state(await runtime.feature_flags().get("openspec-state"))
    assert state.validated is True
    assert state.version == "1.2.3"
    await activation.unsubscribe()


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
async def test_error_guidance_follows_explicit_cli_initialisation_remediation(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)

    ordinary_error = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-status.json", "content": json.dumps({"error": "Unknown change", "message": "Missing"})},
    )
    assert ordinary_error is not None
    assert ordinary_error.rendered_content.content == "Unknown change: Missing"

    root_error = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {
            "path": ".openspec-status.json",
            "content": json.dumps(
                {
                    "error": "No OpenSpec root found from the current directory.",
                    "message": "Fix: Run openspec init to create a root here.",
                }
            ),
        },
    )
    assert root_error is not None
    assert root_error.rendered_content.content.endswith("init-advised")


@pytest.mark.anyio
@pytest.mark.parametrize("empty", [False, True], ids=["grouped", "empty"])
async def test_changes_grouping_and_ttl_expiry(openspec_session, monkeypatch, empty):
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
    request_id = task.prepare_changes_refresh()
    result = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": json.dumps({"changes": changes}), "request_id": request_id},
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
    assert task.get_changes() == grouped
    now += 3600
    assert task.get_changes() is None
    assert not task.is_cache_valid()


@pytest.mark.anyio
async def test_changes_cache_accepts_correlated_cli_response_without_directory_metadata(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    changes = {"changes": []}

    request_id = task.prepare_changes_refresh()
    await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": json.dumps(changes), "request_id": request_id},
    )
    assert task.is_cache_valid()


@pytest.mark.anyio
async def test_expired_changes_cache_rebuilds_openspec_template_context(openspec_session, monkeypatch):
    now = 1_000.0
    monkeypatch.setattr("time.time", lambda: now)
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    changes = [{"name": "active", "status": "in-progress", "completedTasks": 0, "totalTasks": 1}]

    request_id = task.prepare_changes_refresh()
    await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": json.dumps({"changes": changes}), "request_id": request_id},
    )
    cached_context = await get_template_contexts(openspec_session)
    assert cached_context["openspec"]["changes"]

    now += 3601

    refreshed_context = await get_template_contexts(openspec_session)
    assert refreshed_context is not cached_context
    assert refreshed_context["openspec"]["changes"] == []


@pytest.mark.anyio
async def test_changes_cache_is_not_carried_to_a_replacement_task(openspec_session):
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    request_id = task.prepare_changes_refresh()
    await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": '{"changes": []}', "request_id": request_id},
    )
    assert task.is_cache_valid()

    replacement = OpenSpecTask()
    replacement.activation = TaskActivation(manager, replacement, openspec_session)
    replacement._session = openspec_session
    task.activation.retire()

    assert replacement.get_changes() is None


@pytest.mark.anyio
async def test_superseded_changes_refresh_response_is_ignored(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    first_request_id = task.prepare_changes_refresh()

    current_request_id = task.prepare_changes_refresh(force=True)
    stale = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {
            "path": ".openspec-changes.json",
            "content": '{"changes": [{"name": "stale", "status": "in-progress"}]}',
            "request_id": first_request_id,
        },
    )
    assert stale is not None
    assert not stale.result
    assert task.get_changes() is None

    await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {
            "path": ".openspec-changes.json",
            "content": '{"changes": [{"name": "current", "status": "in-progress"}]}',
            "request_id": current_request_id,
        },
    )
    changes = task.get_changes()
    assert changes is not None
    assert changes["in_progress"][0]["name"] == "current"


@pytest.mark.anyio
async def test_unusable_changes_responses_fail_without_changing_the_cache(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    cached_request_id = task.prepare_changes_refresh()
    cached = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {
            "path": ".openspec-changes.json",
            "content": '{"changes": [{"name": "known", "status": "in-progress"}]}',
            "request_id": cached_request_id,
        },
    )
    assert cached is not None and cached.result
    expected_changes = task.get_changes()
    assert expected_changes is not None

    request_id = task.prepare_changes_refresh()

    missing_request_id = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": '{"changes": []}'},
    )
    assert missing_request_id is not None
    assert not missing_request_id.result
    assert task.changes_refresh_id == request_id
    assert task.get_changes() == expected_changes

    malformed = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": "not JSON", "request_id": request_id},
    )
    assert malformed is not None
    assert not malformed.result
    assert task.changes_refresh_id == request_id
    assert task.get_changes() == expected_changes

    invalid_shape = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": '{"changes": {}}', "request_id": request_id},
    )
    assert invalid_shape is not None
    assert not invalid_shape.result
    assert "`changes` must be a list" in invalid_shape.message
    assert task.changes_refresh_id == request_id
    assert task.get_changes() == expected_changes


@pytest.mark.anyio
async def test_recognised_structured_responses_report_the_expected_shape(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)

    result = await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-info.json", "content": '["not", "an", "object"]'},
    )

    assert result is not None
    assert not result.result
    assert result.message == "OpenSpec response `.openspec-info.json` is invalid: expected a JSON object"


@pytest.mark.anyio
async def test_mutation_command_dispatch_invalidates_cached_openspec_results(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    request_id = task.prepare_changes_refresh()
    await task.handle_event(
        EventType.FS_FILE_CONTENT,
        {"path": ".openspec-changes.json", "content": '{"changes": []}', "request_id": request_id},
    )
    openspec_session.task_manager.set_cached_data("openspec_status", {"changeName": "known"})
    openspec_session.task_manager.set_cached_data("openspec_show", {"id": "known"})
    request_context = await request_context_for(openspec_session)

    result = await handle_command("openspec/archive", request_context=request_context, middleware=[])

    assert result.success
    assert task.get_changes() is None
    assert task.get_status() is None
    assert task.get_show() is None
    assert task.changes_refresh_id is None


@pytest.mark.anyio
async def test_openspec_list_command_renders_its_refresh_identifier(openspec_session):
    task = openspec_session.task_manager.get_task_by_type(OpenSpecTask)
    request_context = await request_context_for(openspec_session)

    first = await handle_command("openspec/list", request_context=request_context, middleware=[])
    assert first.success
    assert first.value == "openspec-changes-1"
    assert task.changes_refresh_id == "openspec-changes-1"

    forced = await handle_command(
        "openspec/list", kwargs={"force": True}, request_context=request_context, middleware=[]
    )
    assert forced.success
    assert forced.value == "openspec-changes-2"
    assert task.changes_refresh_id == "openspec-changes-2"


@pytest.mark.anyio
async def test_unrelated_or_malformed_responses_are_ignored(openspec_session):
    manager = openspec_session.task_manager
    task = manager.get_task_by_type(OpenSpecTask)
    for path, content in [("other.md", "Text"), (".openspec-status.json", "not JSON"), ("other.json", "{}")]:
        assert await task.handle_event(EventType.FS_FILE_CONTENT, {"path": path, "content": content}) is None
    assert manager.is_queue_empty()
    assert task.get_status() is None
    assert task.get_show() is None
