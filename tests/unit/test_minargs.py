"""Tests for minargs frontmatter feature in _execute_command."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastmcp import Context
from mcp_types import InputRequiredResult
from tests.helpers import (
    create_bound_test_session,
    create_unbound_test_session,
    request_context_for,
    runtime_config_dir,
)

from mcp_guide.prompts.guide_prompt import _execute_command
from mcp_guide.result import Result


@pytest.fixture
async def cmd_docroot(runtime, session_temp_dir):
    """Provide a session-backed docroot with a _commands dir."""
    config_dir = runtime_config_dir(runtime)
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text("projects: {}\nfeature_flags: {}\n")
    session = create_unbound_test_session(runtime)
    docroot = Path(await runtime.get_docroot())
    (docroot / "_commands").mkdir(parents=True, exist_ok=True)
    return session, docroot


def _write_template(docroot, minargs):
    with open(f"{docroot}/_commands/test.mustache", "w") as f:
        f.write(f"---\nminargs: {minargs!r}\nusage: ':test <expr>'\n---\nok\n")


async def _run(session, docroot, args, minargs):
    _write_template(docroot, minargs)
    request_context = await request_context_for(session)
    return await _execute_command("test", {}, args, request_context, argv=[":test", *args])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "minargs, args",
    [(1, []), (2, ["expr"])],
    ids=["missing_1", "short_2"],
)
async def test_minargs_rejects_too_few_args(cmd_docroot, minargs, args):
    session, docroot = cmd_docroot
    result = await _run(session, docroot, args, minargs)
    assert isinstance(result, Result)
    assert not result.success
    assert "Missing required argument" in (result.error or "")


@pytest.mark.anyio
async def test_minargs_rejects_direct_command_arguments(cmd_docroot):
    """Prompt arguments honour frontmatter even without a parsed argv."""
    session, docroot = cmd_docroot
    _write_template(docroot, 1)

    result = await _execute_command("test", {}, [], await request_context_for(session))

    assert isinstance(result, Result)
    assert not result.success
    assert "Missing required argument" in (result.error or "")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "minargs, args",
    [(0, []), (1, ["expr"]), (2, ["a", "b"]), ("bad", [])],
    ids=["default", "exact_1", "exact_2", "non_int"],
)
async def test_minargs_allows_sufficient_args(cmd_docroot, minargs, args):
    session, docroot = cmd_docroot
    result = await _run(session, docroot, args, minargs)
    assert result.success, result.error
    assert result.value.strip() == "ok"


def _write_export_skill_fixture(docroot: Path) -> None:
    """Provide one discoverable skill and its export command entrypoint."""
    skills_dir = docroot / "_skills" / "sample" / "status"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "---\n"
        "name: status-snapshot\n"
        "description: Report workflow state.\n"
        "usage: Check the current workflow.\n"
        "---\n"
        "Status instructions.\n"
    )
    command_dir = docroot / "_commands" / "skills"
    command_dir.mkdir(parents=True)
    (command_dir / "export.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  export-skill:\n"
        "    message: Choose one skill.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        skill:\n"
        "          type: string\n"
        "          source: guide-skills\n"
        "      required: [skill]\n"
        "---\n"
        "{{#elicit.export-skill}}Export.{{/elicit.export-skill}}\n"
    )


def _elicitation_context() -> SimpleNamespace:
    return SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )


@pytest.mark.anyio
async def test_skills_export_elicitation_uses_current_metadata_catalogue(cmd_docroot, runtime):
    """Skill export offers the one current visible skill without rendering skill templates."""
    _, docroot = cmd_docroot
    _write_export_skill_fixture(docroot)
    session = await create_bound_test_session(runtime, "skills-export")

    result = await _execute_command(
        "skills/export",
        {},
        [],
        await request_context_for(session),
        argv=[":skills/export"],
        mcp_context=cast(Context, _elicitation_context()),
    )

    assert isinstance(result, InputRequiredResult)
    skill_requests = cast(dict[str, Any], result.input_requests)
    skill_request = skill_requests["export-skill"]
    skill_schema = cast(dict[str, Any], skill_request.params.requested_schema)
    assert skill_schema["properties"]["skill"]["enum"] == ["status-snapshot"]


@pytest.mark.anyio
async def test_skills_export_rejects_unavailable_skill_name(cmd_docroot, runtime):
    """A path name must be present in the current metadata catalogue."""
    _, docroot = cmd_docroot
    _write_export_skill_fixture(docroot)
    session = await create_bound_test_session(runtime, "skills-export-invalid")

    result = await _execute_command(
        "skills/export",
        {},
        ["missing"],
        await request_context_for(session),
        argv=[":skills/export", "missing"],
    )

    assert isinstance(result, Result)
    assert not result.success
    assert result.error == "Unknown or unavailable Guide skill: missing"


@pytest.mark.anyio
async def test_skills_export_rejects_a_skill_keyword(cmd_docroot, runtime):
    """The public command shape accepts a skill name only as one path segment."""
    _, docroot = cmd_docroot
    _write_export_skill_fixture(docroot)
    session = await create_bound_test_session(runtime, "skills-export-keyword")

    result = await _execute_command(
        "skills/export",
        {"skill": "status-snapshot"},
        [],
        await request_context_for(session),
        argv=[":skills/export", "--skill=status-snapshot"],
    )

    assert isinstance(result, Result)
    assert not result.success
    assert result.error == "Skill export accepts the skill name only as a path argument."


@pytest.mark.anyio
async def test_skills_export_requires_a_bound_project(cmd_docroot):
    """The project-local export command returns the standard binding result when unbound."""
    session, docroot = cmd_docroot
    _write_export_skill_fixture(docroot)

    result = await _execute_command(
        "skills/export",
        {},
        ["status-snapshot"],
        await request_context_for(session),
        argv=[":skills/export", "status-snapshot"],
    )

    assert isinstance(result, Result)
    assert not result.success
    assert result.error_type == "no_project"
