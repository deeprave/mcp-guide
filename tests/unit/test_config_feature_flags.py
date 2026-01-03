"""Tests for feature flags functionality through Session."""

import tempfile

import pytest

from mcp_guide.session import Session


class TestFeatureFlagsViaSession:
    """Test feature flags functionality through proper Session interface."""

    @pytest.mark.asyncio
    async def test_get_global_flags_empty_default(self):
        """Test getting global flags returns empty dict by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)

            flags_proxy = session.feature_flags()
            flags = await flags_proxy.list()
            assert flags == {}

    @pytest.mark.asyncio
    async def test_set_and_get_global_flag(self):
        """Test setting and getting global flags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)
            flags_proxy = session.feature_flags()

            # Set a flag
            await flags_proxy.set("test_flag", True)

            # Get all flags
            flags = await flags_proxy.list()
            assert flags == {"test_flag": True}

            # Set another flag
            await flags_proxy.set("string_flag", "test_value")
            flags = await flags_proxy.list()
            assert flags == {"test_flag": True, "string_flag": "test_value"}

    @pytest.mark.asyncio
    async def test_remove_global_flag(self):
        """Test removing global flags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)
            flags_proxy = session.feature_flags()

            # Set flags
            await flags_proxy.set("flag1", True)
            await flags_proxy.set("flag2", False)

            # Remove one flag
            await flags_proxy.remove("flag1")

            flags = await flags_proxy.list()
            assert flags == {"flag2": False}

    @pytest.mark.asyncio
    async def test_get_project_flags_empty_default(self):
        """Test getting project flags returns empty dict by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)

            flags_proxy = session.project_flags("test_project")
            flags = await flags_proxy.list()
            assert flags == {}

    @pytest.mark.asyncio
    async def test_set_and_get_project_flag(self):
        """Test setting and getting project flags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)
            flags_proxy = session.project_flags("test_project")

            # Set a flag
            await flags_proxy.set("project_flag", "value")

            # Get all flags
            flags = await flags_proxy.list()
            assert flags == {"project_flag": "value"}

    @pytest.mark.asyncio
    async def test_remove_project_flag(self):
        """Test removing project flags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Session("test-project", _config_dir_for_tests=temp_dir)
            flags_proxy = session.project_flags("test_project")

            # Set flags
            await flags_proxy.set("flag1", True)
            await flags_proxy.set("flag2", False)

            # Remove one flag
            await flags_proxy.remove("flag1")

            flags = await flags_proxy.list()
            assert flags == {"flag2": False}

    @pytest.mark.asyncio
    async def test_config_persistence(self):
        """Test that configuration persists across sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First session - set flags
            session1 = Session("test-project", _config_dir_for_tests=temp_dir)
            global_proxy1 = session1.feature_flags()
            project_proxy1 = session1.project_flags("test_project")

            await global_proxy1.set("persistent_flag", "test_value")
            await project_proxy1.set("project_persistent", True)

            # Second session - verify persistence
            session2 = Session("test-project", _config_dir_for_tests=temp_dir)
            global_proxy2 = session2.feature_flags()
            project_proxy2 = session2.project_flags("test_project")

            # Verify flags persisted
            global_flags = await global_proxy2.list()
            project_flags = await project_proxy2.list()

            assert global_flags == {"persistent_flag": "test_value"}
            assert project_flags == {"project_persistent": True}
