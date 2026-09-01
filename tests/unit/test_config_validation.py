"""Tests for input validation in config methods."""

import pytest
from pydantic_core import ValidationError
from tests.helpers import create_test_runtime, create_test_session

from mcp_guide.runtime import OwnerKey


class TestConfigValidation:
    """Test input validation in configuration methods."""

    @pytest.mark.anyio
    async def test_set_project_flag_invalid_name(self, tmp_path):
        """Test that project flags reject invalid flag names."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        flags = session.project_flags("test-project")
        with pytest.raises(ValidationError, match="Invalid feature flag name"):
            await flags.set("invalid.name", True)

    @pytest.mark.anyio
    async def test_set_project_flag_invalid_value(self, tmp_path):
        """Test that project flags reject invalid flag values."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        flags = session.project_flags("test-project")
        with pytest.raises(ValidationError):
            await flags.set("valid-name", 123)

    @pytest.mark.anyio
    async def test_valid_inputs_accepted(self, tmp_path):
        """Test that valid inputs are accepted."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        project_flags = session.project_flags("test-project")
        # These should not raise exceptions
        await project_flags.set("valid-name", True)
        await project_flags.set("another_name", "string-value")
        await project_flags.set("boolean-string-flag", "enabled")
        await project_flags.remove("valid-name")
        await project_flags.remove("another_name")

    @pytest.mark.anyio
    async def test_configuration_lookup_requires_an_explicit_root(self, tmp_path):
        """Name-only lookup cannot select another root's configuration."""
        session = create_test_runtime(str(tmp_path)).resolve_session(OwnerKey("test-session"))
        with pytest.raises(ValueError, match="explicitly bound root"):
            await session._config().get_or_create_project_config("test")

    @pytest.mark.anyio
    async def test_project_snapshot_ignores_malformed_or_mismatched_entries(self, tmp_path):
        """Only generated keys with their stored full root hash are selectable."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        config_manager = session._config()
        valid_hash = "a" * 64
        config_manager.config_file.write_text(
            "projects:\n"
            f"  valid-{valid_hash[:8]}:\n"
            "    hash: " + valid_hash + "\n"
            "  null-key:\n"
            "    hash: null\n"
            "  missing-hash:\n"
            "    categories: {}\n"
            "  wrong-key-aaaaaaaa:\n"
            "    hash: " + ("b" * 64) + "\n"
        )
        await config_manager._on_external_change(str(config_manager.config_file))

        projects = await session.get_all_projects()

        assert list(projects) == [f"valid-{valid_hash[:8]}"]

    @pytest.mark.anyio
    async def test_project_snapshot_ignores_non_string_keys(self, tmp_path):
        """Non-string project keys are malformed and should be skipped."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        config_manager = session._config()
        config_manager._ensure_config_dir()
        config_manager.config_file.write_text(
            "projects:\n"
            "  123:\n"
            "    hash: " + ("a" * 64) + "\n"
            "  valid-key:\n"
            "    hash: " + ("b" * 64) + "\n"
            "    categories: {}\n"
        )
        await config_manager._on_external_change(str(config_manager.config_file))

        projects = await session.get_all_projects()
        assert list(projects) == []

    @pytest.mark.anyio
    async def test_clone_source_ignores_hashless_entries_and_uses_first_name_match(self, tmp_path):
        """Clone ignores obsolete entries and takes the first valid matching name."""
        session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
        config_manager = session._config()
        first_hash = "a" * 64
        second_hash = "b" * 64
        config_manager.config_file.write_text(
            "projects:\n"
            "  xyz:\n"
            "    categories: {}\n"
            f"  xyz-{first_hash[:8]}:\n"
            f"    hash: {first_hash}\n"
            "    categories: {}\n"
        )
        await config_manager._on_external_change(str(config_manager.config_file))

        source, matches = await session.resolve_clone_source("xyz")
        assert source is not None
        assert source.key == f"xyz-{first_hash[:8]}"
        assert source.hash == first_hash
        assert matches == []

        config_manager.config_file.write_text(
            f"projects:\n  xyz-{first_hash[:8]}:\n    hash: {first_hash}\n    categories: {{}}\n"
        )
        await config_manager._on_external_change(str(config_manager.config_file))
        source, matches = await session.resolve_clone_source("xyz")
        assert source is not None
        assert source.key == f"xyz-{first_hash[:8]}"
        assert matches == []

        config_manager.config_file.write_text(
            "projects:\n"
            f"  xyz-{first_hash[:8]}:\n"
            f"    hash: {first_hash}\n"
            "    categories: {}\n"
            f"  xyz-{second_hash[:8]}:\n"
            f"    hash: {second_hash}\n"
            "    categories: {}\n"
        )
        await config_manager._on_external_change(str(config_manager.config_file))
        source, matches = await session.resolve_clone_source("xyz")
        assert source is not None
        assert source.key == f"xyz-{first_hash[:8]}"
        assert matches == []
