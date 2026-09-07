"""Tests for minargs frontmatter feature in _execute_command."""

from pathlib import Path

import pytest
from tests.helpers import create_unbound_test_session, request_context_for, runtime_config_dir

from mcp_guide.prompts.guide_prompt import _execute_command


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
