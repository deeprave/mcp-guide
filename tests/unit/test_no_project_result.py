"""No-project guidance works without resolving or constructing a Session."""

import json
from types import SimpleNamespace

import pytest

from mcp_guide.core.tool_decorator import _check_project_bound
from mcp_guide.result_constants import AGENT_ERROR, ERROR_NO_PROJECT, INSTRUCTION_NO_PROJECT, make_no_project_result


@pytest.mark.anyio
async def test_unbound_guidance_falls_back_without_a_runtime_and_bound_contexts_pass():
    # No GuideRuntime is installed in this unit test, so this exercises the
    # fallback to the static instruction rather than the rendered template.
    result = await make_no_project_result()
    assert result.error_type == ERROR_NO_PROJECT
    assert result.disposition == AGENT_ERROR
    assert result.instruction == INSTRUCTION_NO_PROJECT

    assert await _check_project_bound(SimpleNamespace(is_bound=True)) is None
    response = await _check_project_bound(SimpleNamespace(is_bound=False))
    assert response.is_error is True
    assert response.structured_content == result.to_json()
    assert json.loads(response.content[0].text) == result.to_json()


@pytest.mark.anyio
async def test_unbound_guidance_renders_project_root_template_once(runtime):
    result = await make_no_project_result()
    assert result.error_type == ERROR_NO_PROJECT
    assert result.disposition == AGENT_ERROR
    assert result.instruction != INSTRUCTION_NO_PROJECT

    # A second call reuses the cached render rather than rendering again.
    again = await make_no_project_result()
    assert again.instruction == result.instruction
