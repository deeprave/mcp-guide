"""Tests for global flags caching in ConfigManager."""

import pytest

from mcp_guide.config import ConfigManager


class TestGlobalFlagsCache:
    """Test global flags caching behavior."""

    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a ConfigManager instance for testing."""
        return ConfigManager(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_global_flags_cached_after_first_read(self, config_manager):
        """Test that global flags are cached after first read."""
        # First call should read from file and cache
        flags1 = await config_manager.get_feature_flags()
        assert flags1 == {}
        assert config_manager._cached_global_flags == {}

        # Second call should return cached value
        flags2 = await config_manager.get_feature_flags()
        assert flags2 == {}
        assert flags2 is config_manager._cached_global_flags

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_set_flag(self, config_manager):
        """Test that cache is invalidated after setting a flag."""
        # Read flags to populate cache
        await config_manager.get_feature_flags()
        assert config_manager._cached_global_flags == {}

        # Set a flag - should invalidate cache
        await config_manager.set_feature_flag("test-flag", True)
        assert config_manager._cached_global_flags is None

        # Next read should populate cache with new value
        flags = await config_manager.get_feature_flags()
        assert flags == {"test-flag": True}
        assert config_manager._cached_global_flags == {"test-flag": True}

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_remove_flag(self, config_manager):
        """Test that cache is invalidated after removing a flag."""
        # Set a flag first
        await config_manager.set_feature_flag("test-flag", True)

        # Read flags to populate cache
        flags = await config_manager.get_feature_flags()
        assert flags == {"test-flag": True}
        assert config_manager._cached_global_flags == {"test-flag": True}

        # Remove the flag - should invalidate cache
        await config_manager.remove_feature_flag("test-flag")
        assert config_manager._cached_global_flags is None

        # Next read should populate cache with updated value
        flags = await config_manager.get_feature_flags()
        assert flags == {}
        assert config_manager._cached_global_flags == {}
