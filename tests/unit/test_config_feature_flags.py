"""Tests for feature flags functionality through Session."""

from pathlib import Path

import pytest
from tests.helpers import (
    bind_isolated_test_session,
    create_bound_test_session,
    create_test_runtime,
    create_unbound_test_session,
)

from mcp_guide.runtime import get_runtime


def _prepare_runtime(config_dir: Path):
    """Install a runtime after writing a minimal config that skips first-run install."""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text("feature_flags: {}\nprojects: {}\n")
    return create_test_runtime(str(config_dir))


class TestFeatureFlagsViaSession:
    """Test process-global feature flags through get_runtime()."""

    @pytest.mark.anyio
    async def test_get_global_flags_empty_default(self, tmp_path):
        """Test getting global flags returns empty dict by default."""
        session = create_unbound_test_session(_prepare_runtime(tmp_path))

        flags_proxy = get_runtime().feature_flags()
        flags = await flags_proxy.list()
        assert flags == {}

    @pytest.mark.anyio
    async def test_set_and_get_global_flag(self, tmp_path):
        """Test setting and getting global flags."""
        session = create_unbound_test_session(_prepare_runtime(tmp_path))
        flags_proxy = get_runtime().feature_flags()

        await flags_proxy.set("test_flag", True)
        flags = await flags_proxy.list()
        assert flags == {"test_flag": True}

        await flags_proxy.set("string_flag", "test_value")
        flags = await flags_proxy.list()
        assert flags == {"test_flag": True, "string_flag": "test_value"}

    @pytest.mark.anyio
    async def test_set_and_get_structured_openspec_state(self, tmp_path):
        """Test the global OpenSpec state round-trips through feature flags."""
        create_unbound_test_session(_prepare_runtime(tmp_path))
        flags_proxy = get_runtime().feature_flags()
        state = {"validated": "true", "version": "1.10.0", "checked": "100.0"}

        await flags_proxy.set("openspec-state", state)

        assert await flags_proxy.get("openspec-state") == state

    @pytest.mark.anyio
    async def test_remove_global_flag(self, tmp_path):
        """Test removing global flags."""
        session = create_unbound_test_session(_prepare_runtime(tmp_path))
        flags_proxy = get_runtime().feature_flags()

        await flags_proxy.set("flag1", True)
        await flags_proxy.set("flag2", False)
        await flags_proxy.remove("flag1")

        flags = await flags_proxy.list()
        assert flags == {"flag2": False}

    @pytest.mark.anyio
    async def test_get_project_flags_empty_default(self, tmp_path):
        """Test getting project flags returns empty dict by default."""
        session = await create_bound_test_session(_prepare_runtime(tmp_path), "test-project")

        flags_proxy = session.project_flags("test_project")
        flags = await flags_proxy.list()
        assert flags == {}

    @pytest.mark.anyio
    async def test_set_and_get_project_flag(self, tmp_path):
        """Test setting and getting project flags."""
        session = await create_bound_test_session(_prepare_runtime(tmp_path), "test-project")
        flags_proxy = session.project_flags("test_project")

        await flags_proxy.set("project_flag", "value")
        flags = await flags_proxy.list()
        assert flags == {"project_flag": "value"}

    @pytest.mark.anyio
    async def test_remove_project_flag(self, tmp_path):
        """Test removing project flags."""
        session = await create_bound_test_session(_prepare_runtime(tmp_path), "test-project")
        flags_proxy = session.project_flags("test_project")

        await flags_proxy.set("flag1", True)
        await flags_proxy.set("flag2", False)
        await flags_proxy.remove("flag1")

        flags = await flags_proxy.list()
        assert flags == {"flag2": False}

    @pytest.mark.anyio
    async def test_config_persistence(self, tmp_path):
        """Test that configuration persists across sessions."""
        runtime = _prepare_runtime(tmp_path)

        session1 = await create_bound_test_session(runtime, "test-project")
        global_proxy1 = get_runtime().feature_flags()
        project_proxy1 = session1.project_flags("test_project")

        await global_proxy1.set("persistent_flag", "test_value")
        await project_proxy1.set("project_persistent", True)

        session2 = await bind_isolated_test_session(runtime, project_name="test-project")
        global_proxy2 = get_runtime().feature_flags()
        project_proxy2 = session2.project_flags("test_project")

        global_flags = await global_proxy2.list()
        project_flags = await project_proxy2.list()

        assert global_flags == {"persistent_flag": "test_value"}
        assert project_flags == {"project_persistent": True}
