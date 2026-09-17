"""Feature flag CRUD and persistence through real runtime and session configuration."""

from pathlib import Path

import pytest
import yaml
from pydantic_core import ValidationError
from tests.helpers import bind_isolated_test_session, create_bound_test_session, create_test_runtime

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import FlagValidationError


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


@pytest.mark.anyio
async def test_project_flag_api_rejects_global_only_mcp_skills_flag(tmp_path):
    """The project-scoped setter enforces the startup-only flag boundary."""
    runtime = _prepare_runtime(tmp_path)
    session = await create_bound_test_session(runtime, "test-project")

    with pytest.raises(FlagValidationError, match="Cannot set project flag `mcp-skills`"):
        await session.project_flags().set("mcp-skills", True)


@pytest.mark.anyio
async def test_global_mcp_skills_flag_accepts_boolean_values(tmp_path):
    """The experiment can be configured only through global feature flags."""
    runtime = _prepare_runtime(tmp_path)

    await runtime.feature_flags().set("mcp-skills", "enabled")

    assert await runtime.feature_flags().get("mcp-skills") == FeatureValue(True)


def test_project_configuration_rejects_global_only_mcp_skills_flag() -> None:
    """MCP capability negotiation cannot be selected by one project."""
    from mcp_guide.models import Project

    with pytest.raises(ValidationError, match="Cannot set project flag `mcp-skills`"):
        Project(name="test-project", project_flags={"mcp-skills": True})
