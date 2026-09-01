"""Tests for minargs frontmatter feature in _execute_command."""

import os

import pytest
from tests.helpers import create_unbound_test_session

from mcp_guide.prompts.guide_prompt import _execute_command


@pytest.fixture
async def cmd_docroot(session_temp_dir):
    """Provide a session-backed docroot with a _commands dir."""
    session = create_unbound_test_session(str(session_temp_dir / "config"))
    docroot = await session.runtime.get_docroot()
    os.makedirs(f"{docroot}/_commands", exist_ok=True)
    return session, docroot


def _write_template(docroot, minargs):
    with open(f"{docroot}/_commands/test.mustache", "w") as f:
        f.write(f"---\nminargs: {minargs!r}\nusage: ':test <expr>'\n---\nok\n")


async def _run(session, docroot, args, minargs):
    _write_template(docroot, minargs)
    return await _execute_command("test", {}, args, None, session, argv=[":test", *args])


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
    assert "Missing required argument" not in (result.error or "")
