"""Integration tests for project resolution with hash disambiguation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mcp_guide.session import Session


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
                    "my-project-abcdef12": {
                        "name": "my-project",
                        "hash": "abcdef1234567890" * 4,
                        "categories": {},
                        "collections": {},
                    }
                },
            }
            config_file.write_text(yaml.dump(config))

            session = Session("my-project", _config_dir_for_tests=tmp_dir)
            project = await session.get_project()

            assert project.name == "my-project"

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
                        "name": "my-project",
                        "hash": "abcdef1234567890" * 4,
                        "categories": {},
                        "collections": {},
                    },
                    "my-project-fedcba98": {
                        "name": "my-project",
                        "hash": "fedcba0987654321" * 4,
                        "categories": {},
                        "collections": {},
                    },
                },
            }
            config_file.write_text(yaml.dump(config))

            # Create session - it should resolve to the correct project based on hash
            with patch("mcp_guide.session.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.return_value = "/some/path"

                with patch("mcp_guide.session.calculate_project_hash") as mock_calc_hash:
                    # Return hash that matches second project
                    mock_calc_hash.return_value = "fedcba0987654321" * 4

                    session = Session("my-project", _config_dir_for_tests=tmp_dir)
                    project = await session.get_project()

                    assert project.name == "my-project"
                    assert project.hash == "fedcba0987654321" * 4

    @pytest.mark.asyncio
    async def test_no_matching_project_creation(self):
        """Non-existent project name creates new project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create empty config
            config = {"docroot": str(tmp_dir), "projects": {}}
            config_file.write_text(yaml.dump(config))

            session = Session("new-project", _config_dir_for_tests=tmp_dir)
            project = await session.get_project()

            assert project.name == "new-project"
            assert project.hash is not None  # Should have calculated a hash

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

            # Mock path resolution to return different hash
            with patch("mcp_guide.session.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.return_value = "/different/path"

                with patch("mcp_guide.session.calculate_project_hash") as mock_calc_hash:
                    # Return different hash
                    mock_calc_hash.return_value = "different_hash_value" * 4

                    session = Session("my-project", _config_dir_for_tests=tmp_dir)
                    session = Session("my-project", _config_dir_for_tests=tmp_dir)
                    project = await session.get_project()

                    # Should create new project with different hash
                    assert project.name == "my-project"
                    assert project.hash == "different_hash_value" * 4

    @pytest.mark.asyncio
    async def test_path_resolution_failure_fallback(self):
        """Path resolution failure falls back gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create config with multiple projects
            config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "my-project-abcdef12": {
                        "name": "my-project",
                        "hash": "abcdef1234567890" * 4,
                        "categories": {},
                        "collections": {},
                    },
                    "my-project-fedcba98": {
                        "name": "my-project",
                        "hash": "fedcba0987654321" * 4,
                        "categories": {},
                        "collections": {},
                    },
                },
            }
            config_file.write_text(yaml.dump(config))

            # Mock path resolution to fail
            with patch("mcp_guide.mcp_context.resolve_project_path") as mock_resolve_path:
                mock_resolve_path.side_effect = ValueError("Cannot determine path")

                session = Session("my-project", _config_dir_for_tests=tmp_dir)
                project = await session.get_project()

                # Should still work - will use fallback path for hash calculation
                assert project.name == "my-project"

    @pytest.mark.asyncio
    async def test_config_error_fallback(self):
        """Configuration errors fall back gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Don't create config file to trigger error handling
            session = Session("my-project", _config_dir_for_tests=tmp_dir)
            project = await session.get_project()

            # Should create new project even with missing config
            assert project.name == "my-project"
