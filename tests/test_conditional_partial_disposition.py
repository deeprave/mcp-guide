"""A conditionally-referenced partial can override the parent's disposition.

Exercises the mechanism status.mustache relies on (a user/information document whose
disposition switches to agent/instruction via an included partial) using synthetic
templates only, independent of any production template's actual content.

A partial contributes its frontmatter (and thus its disposition) exactly when Chevron
accesses its {{>name}} reference during rendering - the condition therefore has to gate
the reference itself, not just content inside the partial's own body (a partial that is
always referenced but renders empty internally still contributes).
"""

from datetime import datetime

import pytest
import yaml

from mcp_guide.core.path_security import resolve_safe_path
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.template import render_template
from tests.helpers import create_unbound_test_session


async def _render(runtime, tmp_path, *, flag_enabled: bool, condition_met: bool):
    runtime.configuration_service().config_file.write_text("projects: {}\n")

    parent_metadata = {"type": "user/information", "includes": ["_setup-needed"]}
    (tmp_path / "parent.mustache").write_text(
        "---\n" + yaml.safe_dump(parent_metadata) + "---\nBody{{^condition_met}}{{>setup-needed}}{{/condition_met}}"
    )

    partial_metadata = {"type": "agent/instruction", "requires-workflow": True}
    (tmp_path / "_setup-needed.mustache").write_text(
        "---\n" + yaml.safe_dump(partial_metadata) + "---\nSetup instruction"
    )

    parent_file = tmp_path / "parent.mustache"
    stat = parent_file.stat()
    info = FileInfo(parent_file, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), "parent")

    from mcp_guide.render.context import TemplateContext

    return await render_template(
        create_unbound_test_session(runtime),
        info,
        tmp_path,
        {"workflow": flag_enabled},
        context=TemplateContext({"condition_met": condition_met, "workflow": flag_enabled}),
        resolver=lambda path: resolve_safe_path(tmp_path, path),
    )


@pytest.mark.anyio
async def test_gated_partial_omitted_when_flag_disabled(runtime, tmp_path):
    result = await _render(runtime, tmp_path, flag_enabled=False, condition_met=False)
    assert result is not None
    assert result.disposition == "user/information"


@pytest.mark.anyio
async def test_gated_partial_contributes_higher_precedence_disposition_when_content_renders(runtime, tmp_path):
    result = await _render(runtime, tmp_path, flag_enabled=True, condition_met=False)
    assert result is not None
    assert result.disposition == "agent/instruction"


@pytest.mark.anyio
async def test_gated_partial_contributes_nothing_when_its_reference_is_not_reached(runtime, tmp_path):
    result = await _render(runtime, tmp_path, flag_enabled=True, condition_met=True)
    assert result is not None
    assert result.disposition == "user/information"
