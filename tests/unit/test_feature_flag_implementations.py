"""Tests for ProjectFlags and GlobalFlags implementations."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_guide.feature_flags.global_flags import GlobalFlags
from mcp_guide.feature_flags.project_flags import ProjectFlags


class TestProjectFlags:
    """Test ProjectFlags implementation."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = MagicMock()
        session.get_project = AsyncMock()
        return session

    @pytest.fixture
    def project_flags(self, mock_session):
        """Create ProjectFlags instance."""
        return ProjectFlags(mock_session)

    @pytest.mark.asyncio
    async def test_get_with_existing_flag(self, project_flags, mock_session):
        """Test get() returns existing flag value."""
        # Setup mock project with flags
        mock_project = MagicMock()
        mock_project.project_flags = {"test_flag": True, "debug_mode": False}
        mock_session.get_project.return_value = mock_project

        # Test getting existing flag
        result = await project_flags.get("test_flag")
        assert result is True

        # Test getting flag that's explicitly False
        result = await project_flags.get("debug_mode")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_with_missing_flag_no_default(self, project_flags, mock_session):
        """Test get() returns None for missing flag when no default provided."""
        # Setup mock project with empty flags
        mock_project = MagicMock()
        mock_project.project_flags = {}
        mock_session.get_project.return_value = mock_project

        # Test getting missing flag
        result = await project_flags.get("missing_flag")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_missing_flag_with_default(self, project_flags, mock_session):
        """Test get() returns default for missing flag when default provided."""
        # Setup mock project with empty flags
        mock_project = MagicMock()
        mock_project.project_flags = {}
        mock_session.get_project.return_value = mock_project

        # Test getting missing flag with truthy defaults
        result = await project_flags.get("missing_flag", True)
        assert result is True

        result = await project_flags.get("missing_flag", "default_value")
        assert result == "default_value"

        # Test getting missing flag with falsy defaults
        result = await project_flags.get("missing_flag", False)
        assert result is False

        result = await project_flags.get("missing_flag", 0)
        assert result == 0

        result = await project_flags.get("missing_flag", "")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_existing_flag_ignores_default(self, project_flags, mock_session):
        """Test get() returns existing value even when default provided."""
        # Setup mock project with flags
        mock_project = MagicMock()
        mock_project.project_flags = {"test_flag": False}
        mock_session.get_project.return_value = mock_project

        # Test that existing False value is returned, not default
        result = await project_flags.get("test_flag", True)
        assert result is False  # Should return False, not True


class TestGlobalFlags:
    """Test GlobalFlags implementation."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        config_manager = MagicMock()
        config_manager.get_feature_flags = AsyncMock()
        return config_manager

    @pytest.fixture
    def global_flags(self, mock_config_manager):
        """Create GlobalFlags instance."""
        return GlobalFlags(mock_config_manager)

    @pytest.mark.asyncio
    async def test_get_with_existing_flag(self, global_flags, mock_config_manager):
        """Test get() returns existing flag value."""
        # Setup mock config manager with flags
        mock_config_manager.get_feature_flags.return_value = {"test_flag": True, "debug_mode": False}

        # Test getting existing flag
        result = await global_flags.get("test_flag")
        assert result is True

        # Test getting flag that's explicitly False
        result = await global_flags.get("debug_mode")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_with_missing_flag_no_default(self, global_flags, mock_config_manager):
        """Test get() returns None for missing flag when no default provided."""
        # Setup mock config manager with empty flags
        mock_config_manager.get_feature_flags.return_value = {}

        # Test getting missing flag
        result = await global_flags.get("missing_flag")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_missing_flag_with_default(self, global_flags, mock_config_manager):
        """Test get() returns default for missing flag when default provided."""
        # Setup mock config manager with empty flags
        mock_config_manager.get_feature_flags.return_value = {}

        # Test getting missing flag with truthy defaults
        result = await global_flags.get("missing_flag", True)
        assert result is True

        result = await global_flags.get("missing_flag", "default_value")
        assert result == "default_value"

        # Test getting missing flag with falsy defaults
        result = await global_flags.get("missing_flag", False)
        assert result is False

        result = await global_flags.get("missing_flag", 0)
        assert result == 0

        result = await global_flags.get("missing_flag", "")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_existing_flag_ignores_default(self, global_flags, mock_config_manager):
        """Test get() returns existing value even when default provided."""
        # Setup mock config manager with flags
        mock_config_manager.get_feature_flags.return_value = {"test_flag": False}

        # Test that existing False value is returned, not default
        result = await global_flags.get("test_flag", True)
        assert result is False  # Should return False, not True
