"""Resolved styling flags control the actual layered template context."""

from unittest.mock import AsyncMock, patch

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.render.cache import TemplateContextCache, get_template_contexts


@pytest.mark.anyio
@pytest.mark.parametrize("style", [None, "plain", "headings", "full", "invalid"])
async def test_styling_from_configuration(style, runtime):
    flags = {} if style is None else {"content-style": style}
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"projects": {}, "feature_flags": flags}))
    session = await create_bound_test_session(runtime, "styling")
    context = await get_template_contexts(session)
    assert context["b"] == ("**" if style == "full" else "")
    assert context["i"] == ("*" if style == "full" else "")
    for level in range(1, 7):
        assert context[f"h{level}"] == ("#" * level + " " if style in ("headings", "full") else "")


@pytest.mark.anyio
async def test_unbound_or_failed_flag_resolution_uses_plain_styling(runtime):
    runtime.configuration_service().config_file.write_text("projects: {}\nfeature_flags: {}\n")
    session = await create_bound_test_session(runtime, "styling")
    unbound = await TemplateContextCache().get_template_contexts()
    # A deterministic dependency failure exercises the fallback without corrupting real configuration.
    with patch("mcp_guide.models.resolve_all_flags", new=AsyncMock(side_effect=ConnectionError("Unavailable"))):
        failed = await get_template_contexts(session)
    for context in (unbound, failed):
        assert {key: context[key] for key in ("b", "i", "h1", "h2", "h3", "h4", "h5", "h6")} == {
            key: "" for key in ("b", "i", "h1", "h2", "h3", "h4", "h5", "h6")
        }
