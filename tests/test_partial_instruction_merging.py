"""Rendered partial instructions obey importance, defaults and deduplication."""

from datetime import datetime

import pytest
import yaml

from mcp_guide.core.path_security import resolve_safe_path
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.template import render_template
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY
from tests.helpers import create_unbound_test_session


@pytest.mark.anyio
@pytest.mark.parametrize(
    "parent,children,expected",
    [
        (
            {"instruction": "Parent instruction"},
            [{"instruction": "Child regular instruction"}],
            "Parent instruction\nChild regular instruction",
        ),
        (
            {"instruction": "Parent instruction"},
            [{"instruction": "Child regular"}, {"instruction": "^ Child important"}],
            "Child important",
        ),
        (
            {"instruction": "Parent instruction"},
            [{"type": "user/information"}],
            "Parent instruction\n" + INSTRUCTION_DISPLAY_ONLY.replace(". ", ".\n"),
        ),
        (
            {"type": "user/information"},
            [{"instruction": "Child instruction"}],
            INSTRUCTION_DISPLAY_ONLY.replace(". ", ".\n") + "\nChild instruction",
        ),
        (
            {"instruction": "Follow this policy."},
            [{"instruction": "Follow this policy."}, {"instruction": "Follow this policy"}],
            "Follow this policy.",
        ),
    ],
    ids=["regular-combined", "important-overrides-all", "child-default", "parent-default", "fuzzy-deduplication"],
)
async def test_partial_instruction_merging(runtime, tmp_path, parent, children, expected):
    runtime.configuration_service().config_file.write_text("projects: {}\n")
    names = [f"child{index}" for index in range(len(children))]
    parent_file = tmp_path / "parent.mustache"
    metadata = {"type": "agent/instruction", **parent, "includes": names}
    parent_file.write_text(
        "---\n" + yaml.safe_dump(metadata) + "---\n" + "".join("{{>" + name + "}}" for name in names)
    )
    for name, child in zip(names, children):
        (tmp_path / f"_{name}.mustache").write_text(
            "---\n" + yaml.safe_dump({"type": "agent/instruction", **child}) + "---\n" + name
        )
    stat = parent_file.stat()
    info = FileInfo(parent_file, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), "parent")
    result = await render_template(
        create_unbound_test_session(runtime),
        info,
        tmp_path,
        {},
        resolver=lambda path: resolve_safe_path(tmp_path, path),
    )
    assert result is not None
    assert result.content == "".join(names)
    assert result.instruction == expected
