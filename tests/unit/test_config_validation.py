"""Tests for input validation in config methods."""

import pytest
from pydantic_core import ValidationError

from mcp_guide.session import Session


class TestConfigValidation:
    """Test input validation in configuration methods."""

    @pytest.mark.asyncio
    async def test_set_project_flag_invalid_name(self, tmp_path):
        """Test that project flags reject invalid flag names."""
        session = Session("test", _config_dir_for_tests=str(tmp_path))
        flags = session.project_flags("test-project")
        with pytest.raises(ValidationError, match="Invalid feature flag name"):
            await flags.set("invalid.name", True)

    @pytest.mark.asyncio
    async def test_set_project_flag_invalid_value(self, tmp_path):
        """Test that project flags reject invalid flag values."""
        session = Session("test", _config_dir_for_tests=str(tmp_path))
        flags = session.project_flags("test-project")
        with pytest.raises(ValidationError):
            await flags.set("valid-name", 123)

    @pytest.mark.asyncio
    async def test_valid_inputs_accepted(self, tmp_path):
        """Test that valid inputs are accepted."""
        session = Session("test", _config_dir_for_tests=str(tmp_path))
        project_flags = session.project_flags("test-project")
        # These should not raise exceptions
        await project_flags.set("valid-name", True)
        await project_flags.set("another_name", "string-value")
        await project_flags.set("list-flag", ["list", "of", "strings"])
        await project_flags.remove("valid-name")
        await project_flags.remove("another_name")
