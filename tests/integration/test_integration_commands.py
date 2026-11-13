"""Command and content routing through real templates and bound project data."""

import json
from types import SimpleNamespace

import pytest
import yaml
from mcp_types import InputRequiredResult

from mcp_guide.models import Category
from mcp_guide.prompts.guide_prompt import _execute_command, guide, handle_command
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
@pytest.mark.parametrize("prefix", [":", ";"], ids=["colon", "semicolon"])
async def test_command_arguments_render_in_order(command_project, prefix):
    _, invoke = command_project
    result = await invoke(f"{prefix}test", "--verbose", "arg1", "arg2", "arg3")
    assert result["success"] is True
    assert "Test command executed successfully!" in result["value"]
    assert "Verbose mode enabled." in result["value"]
    assert "Args: arg1 arg2 arg3" in result["value"]
    assert "Indexed args: FIRST: arg1 arg2 arg3 LAST" in result["value"]


@pytest.mark.anyio
async def test_content_routing_combines_real_category_expressions(command_project):
    _, invoke = command_project
    single = await invoke("docs")
    assert single["success"] is True
    assert single["value"] == "Content from docs"
    combined = await invoke("docs", "examples", "tests")
    assert combined["success"] is True
    for name in ["docs", "examples", "tests"]:
        assert f"Content from {name}" in combined["value"]
    missing = await invoke("nonexistent")
    assert missing["success"] is False
    assert missing["error"]


@pytest.mark.anyio
async def test_security_rejects_traversal_and_command_injection(command_project):
    _, invoke = command_project
    for command in [":../../../etc/passwd", ":test;rm"]:
        result = await invoke(command)
        assert result["success"] is False
        assert "security validation failed" in result["error"].lower()


@pytest.mark.anyio
async def test_help_discovers_actual_commands(command_project):
    commands, invoke = command_project
    (commands / "help.mustache").write_text(
        "---\ndescription: Show help information\n---\n"
        "Available commands:\n{{#commands}}- {{name}}: {{description}}\n{{/commands}}"
    )
    result = await invoke(":help")
    assert result["success"] is True
    assert "Available commands:" in result["value"]
    assert "test: Test command" in result["value"]
    assert "help: Show help information" in result["value"]


@pytest.mark.anyio
async def test_help_reports_rendering_diagnostics(command_project):
    commands, invoke = command_project
    (commands / "help.mustache").write_text(
        "---\ndescription: '{{#_error}}Help configuration is invalid{{/_error}}'\n---\nHelp"
    )

    result = await invoke(":help", "test")

    assert result["success"] is False
    assert result["error_type"] == "validation_error"
    assert result["error_data"] == {"errors": ["Frontmatter field 'description': Help configuration is invalid"]}


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
async def test_worktree_use_offers_fresh_linked_worktree_paths(command_project, runtime):
    commands, _ = command_project
    worktree = commands / "worktree"
    worktree.mkdir()
    (worktree / "use.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  worktree-path:\n"
        "    message: Choose a linked worktree.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        worktree_path:\n"
        "          type: string\n"
        "          source: worktree-inventory\n"
        "      required: [worktree_path]\n"
        "---\n"
        "{{#elicit.worktree-path}}Selected {{kwargs.worktree_path}}{{/elicit.worktree-path}}"
    )
    session = await create_bound_test_session(runtime, "worktree-use-select")
    linked = session.bound_root_path.parent / "linked-checkout"
    inventory = await internal_send_file_content(
        SendFileContentArgs(
            path=".git-worktrees.json", content=json.dumps([str(session.bound_root_path), str(linked)])
        ),
        await request_context_for(session),
    )
    assert inventory.success
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await _execute_command("worktree/use", {}, [], await request_context_for(session), mcp_context=context)

    assert isinstance(result, InputRequiredResult)
    assert result.input_requests["worktree-path"].params.requested_schema["properties"]["worktree_path"]["enum"] == [
        str(linked)
    ]


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


@pytest.mark.anyio
async def test_subcommand_partials_use_current_project_context(command_project):
    commands, invoke = command_project
    info = commands / "info"
    partials = commands / "_partials"
    info.mkdir()
    partials.mkdir()
    (partials / "_project.mustache").write_text("Project: {{project.name}}")
    (info / "project.mustache").write_text(
        "---\ntype: user/information\nincludes:\n  - ../_partials/project\n---\nProject Information:\n{{>project}}"
    )
    result = await invoke(":info/project")
    assert result["success"] is True
    assert "Project Information:" in result["value"]
    assert "Project: test-project" in result["value"]


@pytest.mark.anyio
async def test_command_errors_are_returned_in_native_prompt_payload(command_project):
    commands, invoke = command_project
    parse_error = await invoke(":test", "--bad=", "=value")
    assert parse_error["success"] is False
    assert parse_error["error_type"] == "validation_error"
    assert "Argument parsing failed" in parse_error["error"]
    (commands / "broken.mustache").write_text("{{#_error}}Missing required argument: name{{/_error}}")
    rendered_error = await invoke(":broken")
    assert rendered_error["success"] is False
    assert rendered_error["error_type"] == "validation_error"
    assert rendered_error["error_data"]["errors"] == ["Missing required argument: name"]
