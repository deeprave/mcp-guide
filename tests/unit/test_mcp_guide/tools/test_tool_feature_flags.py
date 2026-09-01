"""Tests for global feature-flag tools and runtime-owned flag access."""

import pytest

from mcp_guide.runtime import GuideRuntime


@pytest.mark.anyio
async def test_runtime_global_flags_without_a_session(tmp_path):
    """GuideRuntime owns global flag list/get/set/remove without a Session."""
    (tmp_path / "config.yaml").write_text("feature_flags: {}\nprojects: {}\n")
    runtime = GuideRuntime(lambda _owner: object(), config_dir=str(tmp_path))
    flags = runtime.feature_flags()

    await flags.set("workflow", True)
    assert (await flags.get("workflow")).to_raw() is True
    listed = await flags.list()
    assert listed["workflow"].to_raw() is True

    await flags.remove("workflow")
    assert await flags.get("workflow") is None
