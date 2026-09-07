"""Command and content routing through real templates and bound project data."""

import json

import pytest
import yaml

from mcp_guide.models import Category
from mcp_guide.prompts.guide_prompt import guide
from tests.helpers import create_bound_test_session, request_context_for


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
        "Indexed args: {{#args}}{{#first}}FIRST: {{/first}}{{value}}"
        "{{^last}} {{/last}}{{#last}} LAST{{/last}}{{/args}}"
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
