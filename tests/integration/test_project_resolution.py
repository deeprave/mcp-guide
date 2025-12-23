"""Integration tests for project resolution with hash disambiguation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mcp_guide.config import ConfigManager
from mcp_guide.session import resolve_project_by_name


class TestProjectResolution:
    """Test end-to-end project resolution with hash disambiguation."""

    @pytest.mark.asyncio
    async def test_single_project_resolution(self):
        """Single project with name resolves correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create config with single project
            config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "my-project-abcdef12": {"hash": "abcdef1234567890" * 4, "categories": {}, "collections": {}}
                },
            }
            config_file.write_text(yaml.dump(config))

            config_manager = ConfigManager(config_dir=tmp_dir)
            resolved_name = await resolve_project_by_name("my-project", config_manager)

            assert resolved_name == "my-project"

    @pytest.mark.asyncio
    async def test_multiple_projects_hash_verification(self):
        """Multiple projects with same name resolve by hash."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create the config file with the expected name
            from mcp_guide.config_paths import get_config_file

            config_file = get_config_file(tmp_dir)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Create config with multiple same-named projects
            config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "my-project-abcdef12": {
                        "name": "my-project",  # Add name field
                        "hash": "abcdef1234567890" * 4,
                        "categories": {},
                        "collections": {},
                    },
                    "my-project-fedcba98": {
                        "name": "my-project",  # Add name field
                        "hash": "fedcba0987654321" * 4,
                        "categories": {},
                        "collections": {},
                    },
                },
            }
            config_file.write_text(yaml.dump(config))

            config_manager = ConfigManager(config_dir=tmp_dir)

            # First verify we have multiple projects with same name
            all_projects = await config_manager.get_all_project_configs()
            matching_projects = [proj for proj in all_projects.values() if proj.name == "my-project"]
            assert len(matching_projects) == 2, f"Expected 2 projects, got {len(matching_projects)}"

            # Mock path resolution to return specific hash
            with patch("mcp_guide.session.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.return_value = "/some/path"

                with patch("mcp_guide.utils.project_hash.calculate_project_hash") as mock_calc_hash:
                    # Return hash that matches second project
                    mock_calc_hash.return_value = "fedcba0987654321" * 4

                    resolved_name = await resolve_project_by_name("my-project", config_manager)

                    assert resolved_name == "my-project"
                    # Now the mocks should have been called
                    mock_resolve_path.assert_called_once()
                    mock_calc_hash.assert_called_once_with("/some/path")

    @pytest.mark.asyncio
    async def test_no_matching_project_creation(self):
        """Non-existent project name returns name for creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create empty config
            config = {"docroot": str(tmp_dir), "projects": {}}
            config_file.write_text(yaml.dump(config))

            config_manager = ConfigManager(config_dir=tmp_dir)
            resolved_name = await resolve_project_by_name("new-project", config_manager)

            assert resolved_name == "new-project"

    @pytest.mark.asyncio
    async def test_hash_mismatch_fallback(self):
        """Hash mismatch falls back to name for new project creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create config with project that won't match current hash
            config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "my-project-abcdef12": {"hash": "abcdef1234567890" * 4, "categories": {}, "collections": {}}
                },
            }
            config_file.write_text(yaml.dump(config))

            config_manager = ConfigManager(config_dir=tmp_dir)

            # Mock path resolution to return different hash
            with patch("mcp_guide.session.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.return_value = "/different/path"

                with patch("mcp_guide.utils.project_hash.calculate_project_hash") as mock_calc_hash:
                    # Return different hash
                    mock_calc_hash.return_value = "different_hash_value" * 4

                    resolved_name = await resolve_project_by_name("my-project", config_manager)

                    # Should return name for new project creation
                    assert resolved_name == "my-project"

    @pytest.mark.asyncio
    async def test_path_resolution_failure_fallback(self):
        """Path resolution failure falls back gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create config with multiple projects
            config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "my-project-abcdef12": {"hash": "abcdef1234567890" * 4, "categories": {}, "collections": {}},
                    "my-project-fedcba98": {"hash": "fedcba0987654321" * 4, "categories": {}, "collections": {}},
                },
            }
            config_file.write_text(yaml.dump(config))

            config_manager = ConfigManager(config_dir=tmp_dir)

            # Mock path resolution to fail
            with patch("mcp_guide.session.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.side_effect = ValueError("Cannot determine path")

                resolved_name = await resolve_project_by_name("my-project", config_manager)

                # Should fall back to first match
                assert resolved_name == "my-project"

    @pytest.mark.asyncio
    async def test_config_error_fallback(self):
        """Configuration errors fall back gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Don't create config file to trigger error
            config_manager = ConfigManager(config_dir=tmp_dir)

            resolved_name = await resolve_project_by_name("my-project", config_manager)

            # Should return original name
            assert resolved_name == "my-project"
