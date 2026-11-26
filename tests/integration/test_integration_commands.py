"""Command and content routing through real templates and bound project data."""

import json

import pytest
import yaml

from mcp_guide.models import Category
from mcp_guide.prompts.guide_prompt import guide, handle_command
from mcp_guide.tools.tool_filesystem import SendFileContentArgs, internal_send_file_content
from tests.helpers import create_bound_test_session, create_unbound_test_session, request_context_for


@pytest.fixture
async def command_project(runtime, tmp_path):
    docroot = tmp_path / "docs"
    commands = docroot / "_commands"
    commands.mkdir(parents=True)
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    (commands / "test.mustache").write_text(
        "---\ndescription: Test command\n---\n"
        "Test command executed successfully!\n"
        "{{#kwargs.verbose}}Verbose mode enabled.{{/kwargs.verbose}}\n"
        "Args: {{#args}}{{value}} {{/args}}\n"
        "Indexed args: {{#args}}{{#.first}}FIRST: {{/.first}}{{value}}"
        "{{^.last}} {{/.last}}{{#.last}} LAST{{/.last}}{{/args}}"
    )
    session = await create_bound_test_session(runtime, "test-project")
    for name in ["docs", "examples", "tests"]:
        folder = docroot / name
        folder.mkdir()
        (folder / "overview.md").write_text(f"Content from {name}")
        await session.update_config(lambda p, name=name: p.with_category(name, Category(dir=name, patterns=["*.md"])))

    async def invoke(*args):
        response = await guide.__wrapped__(*args, request_context=await request_context_for(session))
        return json.loads(response.messages[0].content.text)

    return commands, invoke


@pytest.mark.anyio
async def test_worktree_command_reports_incompatible_workflow_file(command_project, runtime):
    commands, _ = command_project
    worktree = commands / "worktree"
    partials = commands / "_partials"
    worktree.mkdir()
    partials.mkdir()
    (partials / "_handoff-target.mustache").write_text("{{handoff_context.target}} ({{handoff_context.format}})")
    (worktree / "new.mustache").write_text(
        "---\nrequires-worktree-support: true\nincludes:\n  - ../_partials/handoff-target\n---\nCreate worktree: {{>handoff-target}}"
    )
    session = await create_bound_test_session(runtime, "worktree-command")
    inventory = await internal_send_file_content(
        SendFileContentArgs(path=".git-worktrees.json", content=json.dumps([str(session.bound_root_path)])),
        await request_context_for(session),
    )
    assert inventory.success

    result = await handle_command("worktree/new", request_context=await request_context_for(session), middleware=[])
    assert result.success
    assert f"{session.bound_root_path}/.todo/context.json (JSON)" in result.value

    await session.project_flags().set("workflow-file", "/shared/.guide.yaml")
    inventory = await internal_send_file_content(
        SendFileContentArgs(path=".git-worktrees.json", content=json.dumps([str(session.bound_root_path)])),
        await request_context_for(session),
    )
    assert inventory.success

    unavailable = await handle_command(
        "worktree/new", request_context=await request_context_for(session), middleware=[]
    )
    assert not unavailable.success
    assert unavailable.error_type == "validation_error"
    assert "workflow-file to be a basename" in unavailable.error


@pytest.mark.anyio
async def test_worktree_use_retains_the_existing_handoff_label(command_project, runtime):
    commands, _ = command_project
    worktree = commands / "worktree"
    worktree.mkdir()
    (worktree / "use.mustache").write_text(
        "---\nrequires-worktree-support: true\nminargs: 1\n---\nUse {{kwargs.worktree_name}} for {{args.0.value}}"
    )
    session = await create_bound_test_session(runtime, "worktree-use")
    inventory = await internal_send_file_content(
        SendFileContentArgs(path=".git-worktrees.json", content=json.dumps([str(session.bound_root_path)])),
        await request_context_for(session),
    )
    assert inventory.success

    result = await handle_command(
        "worktree/use", args=["existing-label"], request_context=await request_context_for(session), middleware=[]
    )

    assert result.success
    assert result.value == "Use existing-label for existing-label"


@pytest.mark.anyio
async def test_worktree_use_rejects_an_invalid_explicit_label(command_project, runtime):
    commands, _ = command_project
    worktree = commands / "worktree"
    worktree.mkdir()
    (worktree / "use.mustache").write_text("Use {{kwargs.worktree_name}}")
    session = await create_bound_test_session(runtime, "worktree-use-invalid")
    inventory = await internal_send_file_content(
        SendFileContentArgs(path=".git-worktrees.json", content=json.dumps([str(session.bound_root_path)])),
        await request_context_for(session),
    )
    assert inventory.success

    result = await handle_command(
        "worktree/use", args=["bad/label"], request_context=await request_context_for(session), middleware=[]
    )

    assert not result.success
    assert "Workflow worktree label" in result.error


@pytest.mark.anyio
async def test_linked_worktree_cannot_start_a_new_handoff(runtime, tmp_path):
    docroot = tmp_path / "docs"
    command_path = docroot / "_commands" / "worktree"
    command_path.mkdir(parents=True)
    (command_path / "new.mustache").write_text("Create a worktree")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    from mcp_guide.session import bind_session_project

    session = create_unbound_test_session(runtime)
    await bind_session_project(session, "/client/project", worktree="/client/project-linked")

    result = await handle_command("worktree/new", request_context=await request_context_for(session), middleware=[])

    assert not result.success
    assert result.error_type == "validation_error"
    assert "root-bound Guide session" in result.error
