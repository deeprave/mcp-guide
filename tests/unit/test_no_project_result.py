"""No-project guidance works without resolving or constructing a Session."""

import json
from types import SimpleNamespace

import pytest

from mcp_guide.core.tool_decorator import _check_project_bound
from mcp_guide.result_constants import RESULT_NO_PROJECT, make_no_project_result


@pytest.mark.anyio
async def test_unbound_guidance_is_static_native_error_and_bound_contexts_pass():
    assert await make_no_project_result() is RESULT_NO_PROJECT
    assert await _check_project_bound(SimpleNamespace(is_bound=True)) is None
    response = await _check_project_bound(SimpleNamespace(is_bound=False))
    assert response.is_error is True
    assert response.structured_content == RESULT_NO_PROJECT.to_json()
    assert json.loads(response.content[0].text) == RESULT_NO_PROJECT.to_json()
