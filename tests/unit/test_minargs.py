"""Tests for minargs frontmatter feature in _execute_command."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp_types import InputRequiredResult
from tests.helpers import (
    create_bound_test_session,
    create_unbound_test_session,
    request_context_for,
    runtime_config_dir,
)

from mcp_guide.prompts.guide_prompt import _execute_command
from mcp_guide.workflow.schema import WorkflowState


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


@pytest.mark.anyio
async def test_execute_command_specialises_workflow_phase_choices(cmd_docroot, runtime):
    """Command execution derives dynamic phase choices before requesting input."""
    _, docroot = cmd_docroot
    session = await create_bound_test_session(runtime, "workflow-input")
    await session.project_flags().set("workflow", True)
    session.task_manager.set_cached_data("workflow_state", WorkflowState(phase="planning"))
    (docroot / "_commands/test.mustache").write_text(
        "---\n"
        "requires-workflow: true\n"
        "elicitation:\n"
        "  workflow-phase:\n"
        "    message: Choose a phase.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        phase:\n"
        "          type: string\n"
        "          source: workflow-phases\n"
        "      required: [phase]\n"
        "---\n"
        "Phase={{kwargs.phase}}\n"
    )
    context = SimpleNamespace(
        session=SimpleNamespace(client_params=SimpleNamespace(capabilities=SimpleNamespace(elicitation={}))),
        input_responses=None,
        request_context=SimpleNamespace(protocol_version="2026-07-28"),
    )

    result = await _execute_command(
        "test",
        {},
        [],
        await request_context_for(session),
        argv=[":test"],
        mcp_context=context,
    )

    assert isinstance(result, InputRequiredResult)
    assert result.input_requests["workflow-phase"].params.requested_schema["properties"]["phase"]["enum"] == [
        "discussion",
        "exploration",
        "implementation",
        "check",
        "review",
    ]
