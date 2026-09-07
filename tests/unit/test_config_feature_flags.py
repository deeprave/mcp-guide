"""Feature flag CRUD and persistence through real runtime and session configuration."""

from pathlib import Path

import pytest
import yaml
from tests.helpers import bind_isolated_test_session, create_bound_test_session, create_test_runtime


def _prepare_runtime(config_dir: Path):
    """Write minimal configuration without invoking the unrelated first-run installer."""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text("feature_flags: {}\nprojects: {}\n")
    return create_test_runtime(str(config_dir))


@pytest.mark.anyio
async def test_global_flags_round_trip_without_a_bound_session(tmp_path):
    runtime = _prepare_runtime(tmp_path)
    flags = runtime.feature_flags()
    assert await flags.list() == {}
    state = {"validated": "true", "version": "1.10.0", "checked": "100.0"}
    await flags.set("test_flag", True)
    await flags.set("string_flag", "test_value")
    await flags.set("openspec-state", state)
    assert await flags.list() == {"test_flag": True, "string_flag": "test_value", "openspec-state": state}
    assert await flags.get("openspec-state") == state

    await flags.remove("test_flag")
    expected = {"string_flag": "test_value", "openspec-state": state}
    assert await flags.list() == expected
    persisted = yaml.safe_load((tmp_path / "config.yaml").read_text())
    assert persisted["feature_flags"] == expected


@pytest.mark.anyio
async def test_project_flags_remain_separate_and_persist_across_sessions(tmp_path):
    runtime = _prepare_runtime(tmp_path)
    session = await create_bound_test_session(runtime, "test-project")
    global_flags = runtime.feature_flags()
    flags = session.project_flags()
    assert await flags.list() == {}
    await global_flags.set("persistent_flag", "test_value")
    await flags.set("project_flag", "value")
    await flags.set("flag1", True)
    await flags.set("flag2", False)
    assert await flags.list() == {"project_flag": "value", "flag1": True, "flag2": False}
    await flags.remove("flag1")
    expected = {"project_flag": "value", "flag2": False}
    assert await flags.list() == expected
    assert await global_flags.list() == {"persistent_flag": "test_value"}

    second = await bind_isolated_test_session(runtime, project_name="test-project")
    assert await second.project_flags().list() == expected
    persisted = yaml.safe_load((tmp_path / "config.yaml").read_text())
    assert persisted["projects"][session.project.key]["project_flags"] == expected
