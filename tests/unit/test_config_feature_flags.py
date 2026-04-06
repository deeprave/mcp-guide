"""Tests for feature flags functionality through Session."""

from pathlib import Path

import pytest
from tests.helpers import create_bound_test_session

from mcp_guide.session import Session


def _prepare_config_dir(config_dir: Path) -> str:
    """Create a minimal config file so tests skip first-run install work."""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text("feature_flags: {}\nprojects: {}\n")
    return str(config_dir)


class TestFeatureFlagsViaSession:
    """Test feature flags functionality through proper Session interface."""

    @pytest.mark.anyio
    async def test_get_global_flags_empty_default(self, tmp_path):
        """Test getting global flags returns empty dict by default."""
        session = Session(_config_dir_for_tests=_prepare_config_dir(tmp_path))

        flags_proxy = session.feature_flags()
        flags = await flags_proxy.list()
        assert flags == {}

    @pytest.mark.anyio
    async def test_set_and_get_global_flag(self, tmp_path):
        """Test setting and getting global flags."""
        session = Session(_config_dir_for_tests=_prepare_config_dir(tmp_path))
        flags_proxy = session.feature_flags()

        await flags_proxy.set("test_flag", True)
        flags = await flags_proxy.list()
        assert flags == {"test_flag": True}

        await flags_proxy.set("string_flag", "test_value")
        flags = await flags_proxy.list()
        assert flags == {"test_flag": True, "string_flag": "test_value"}

    @pytest.mark.anyio
    async def test_remove_global_flag(self, tmp_path):
        """Test removing global flags."""
        session = Session(_config_dir_for_tests=_prepare_config_dir(tmp_path))
        flags_proxy = session.feature_flags()

        await flags_proxy.set("flag1", True)
        await flags_proxy.set("flag2", False)
        await flags_proxy.remove("flag1")

        flags = await flags_proxy.list()
        assert flags == {"flag2": False}

    @pytest.mark.anyio
    async def test_get_project_flags_empty_default(self, tmp_path):
        """Test getting project flags returns empty dict by default."""
        session = await create_bound_test_session("test-project", _config_dir_for_tests=_prepare_config_dir(tmp_path))

        flags_proxy = session.project_flags("test_project")
        flags = await flags_proxy.list()
        assert flags == {}

    @pytest.mark.anyio
    async def test_set_and_get_project_flag(self, tmp_path):
        """Test setting and getting project flags."""
        session = await create_bound_test_session("test-project", _config_dir_for_tests=_prepare_config_dir(tmp_path))
        flags_proxy = session.project_flags("test_project")

        await flags_proxy.set("project_flag", "value")
        flags = await flags_proxy.list()
        assert flags == {"project_flag": "value"}

    @pytest.mark.anyio
    async def test_remove_project_flag(self, tmp_path):
        """Test removing project flags."""
        session = await create_bound_test_session("test-project", _config_dir_for_tests=_prepare_config_dir(tmp_path))
        flags_proxy = session.project_flags("test_project")

        await flags_proxy.set("flag1", True)
        await flags_proxy.set("flag2", False)
        await flags_proxy.remove("flag1")

        flags = await flags_proxy.list()
        assert flags == {"flag2": False}

    @pytest.mark.anyio
    async def test_config_persistence(self, tmp_path):
        """Test that configuration persists across sessions."""
        config_dir = _prepare_config_dir(tmp_path)

        session1 = await create_bound_test_session("test-project", _config_dir_for_tests=config_dir)
        global_proxy1 = session1.feature_flags()
        project_proxy1 = session1.project_flags("test_project")

        await global_proxy1.set("persistent_flag", "test_value")
        await project_proxy1.set("project_persistent", True)

        session2 = await create_bound_test_session("test-project", _config_dir_for_tests=config_dir)
        global_proxy2 = session2.feature_flags()
        project_proxy2 = session2.project_flags("test_project")

        global_flags = await global_proxy2.list()
        project_flags = await project_proxy2.list()

        assert global_flags == {"persistent_flag": "test_value"}
        assert project_flags == {"project_persistent": True}
