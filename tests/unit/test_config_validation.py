"""Tests for input validation in config methods."""

import pytest

from mcp_guide.config import ConfigManager


class TestConfigValidation:
    """Test input validation in configuration methods."""

    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a ConfigManager instance for testing."""
        return ConfigManager(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_set_global_flag_invalid_name(self, config_manager):
        """Test that set_feature_flag rejects invalid flag names."""
        with pytest.raises(ValueError, match="Invalid flag name"):
            await config_manager.set_feature_flag("invalid.name", True)

    @pytest.mark.asyncio
    async def test_set_global_flag_invalid_value(self, config_manager):
        """Test that set_feature_flag rejects invalid flag values."""
        with pytest.raises(ValueError, match="Invalid flag value type"):
            await config_manager.set_feature_flag("valid-name", 123)

    @pytest.mark.asyncio
    async def test_remove_global_flag_invalid_name(self, config_manager):
        """Test that remove_feature_flag rejects invalid flag names."""
        with pytest.raises(ValueError, match="Invalid flag name"):
            await config_manager.remove_feature_flag("invalid.name")

    @pytest.mark.asyncio
    async def test_set_project_flag_invalid_name(self, config_manager):
        """Test that set_project_flag rejects invalid flag names."""
        with pytest.raises(ValueError, match="Invalid flag name"):
            await config_manager.set_project_flag("test-project", "invalid.name", True)

    @pytest.mark.asyncio
    async def test_set_project_flag_invalid_value(self, config_manager):
        """Test that set_project_flag rejects invalid flag values."""
        with pytest.raises(ValueError, match="Invalid flag value type"):
            await config_manager.set_project_flag("test-project", "valid-name", 123)

    @pytest.mark.asyncio
    async def test_remove_project_flag_invalid_name(self, config_manager):
        """Test that remove_project_flag rejects invalid flag names."""
        with pytest.raises(ValueError, match="Invalid flag name"):
            await config_manager.remove_project_flag("test-project", "invalid.name")

    @pytest.mark.asyncio
    async def test_valid_inputs_accepted(self, config_manager):
        """Test that valid inputs are accepted."""
        # These should not raise exceptions
        await config_manager.set_feature_flag("valid-name", True)
        await config_manager.set_feature_flag("another_name", "string-value")
        await config_manager.set_project_flag("test-project", "valid-name", ["list", "of", "strings"])
        await config_manager.remove_feature_flag("valid-name")
        await config_manager.remove_project_flag("test-project", "valid-name")
