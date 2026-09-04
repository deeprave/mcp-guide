"""Integration tests for project resolution with hash disambiguation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from tests.helpers import create_test_runtime, create_test_session


class TestProjectResolution:
    """Test end-to-end project resolution with hash disambiguation."""

    @staticmethod
    def _write_config(config_dir: Path, config: dict) -> Path:
        config_file = config_dir / "guide.yaml"
        config_file.write_text(yaml.dump(config))
        return config_file

    @pytest.mark.anyio
    async def test_single_project_resolution(self, runtime, tmp_path):
        """Single project with name resolves correctly."""
        config = {
            "docroot": str(tmp_path),
            "projects": {
                "my-project-abcdef12": {
                    "name": "my-project",
                    "hash": "abcdef1234567890" * 4,
                    "categories": {},
                    "collections": {},
                }
            },
        }
        self._write_config(tmp_path, config)

        session = await create_test_session(runtime, "my-project")
        project = await session.get_project()

        assert project.name == "my-project"

    @pytest.mark.anyio
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

            # Create session - it should resolve to the correct project based on hash.
            with patch("mcp_guide.configuration.calculate_project_hash") as mock_calc_hash:
                mock_calc_hash.return_value = "fedcba0987654321" * 4

                session = await create_test_session(create_test_runtime(tmp_dir), "my-project")
                project = await session.get_project()

                assert project.name == "my-project"
                assert project.hash == "fedcba0987654321" * 4

    @pytest.mark.anyio
    async def test_no_matching_project_creation(self, runtime, tmp_path):
        """Non-existent project name creates new project."""
        config_file = Path(tmp_path) / "guide.yaml"

        # Create empty config
        config = {"docroot": str(tmp_path), "projects": {}}
        config_file.write_text(yaml.dump(config))

        with patch("mcp_guide.configuration.calculate_project_hash", return_value="new_hash_value" * 4):
            session = await create_test_session(runtime, "new-project")
            project = await session.get_project()

            assert project.name == "new-project"
            assert project.hash == "new_hash_value" * 4

    @pytest.mark.anyio
    async def test_hash_mismatch_fallback(self, runtime, tmp_path):
        """Hash mismatch falls back to name for new project creation."""
        config_file = Path(tmp_path) / "guide.yaml"

        # Create config with project that won't match current hash
        config = {
            "docroot": str(tmp_path),
            "projects": {"my-project-abcdef12": {"hash": "abcdef1234567890" * 4, "categories": {}, "collections": {}}},
        }
        config_file.write_text(yaml.dump(config))

        with patch("mcp_guide.configuration.calculate_project_hash", return_value="different_hash_value" * 4):
            session = await create_test_session(runtime, "my-project")
            project = await session.get_project()

            # Should create new project with different hash
            assert project.name == "my-project"
            assert project.hash == "different_hash_value" * 4

    @pytest.mark.anyio
    async def test_path_resolution_failure_fallback(self, runtime, tmp_path):
        """Path resolution failure falls back gracefully."""
        config = {
            "docroot": str(tmp_path),
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
        self._write_config(tmp_path, config)

        # Mock path resolution to fail
        with patch("mcp_guide.mcp_context.resolve_project_path") as mock_resolve_path:
            mock_resolve_path.side_effect = ValueError("Cannot determine path")

            session = await create_test_session(runtime, "my-project")
            project = await session.get_project()

            # Should still work - will use fallback path for hash calculation
            assert project.name == "my-project"

    @pytest.mark.anyio
    async def test_config_error_fallback(self):
        """Configuration errors fall back gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Don't create config file to trigger error handling
            session = await create_test_session(create_test_runtime(tmp_dir), "my-project")
            project = await session.get_project()

            # Should create new project even with missing config
            assert project.name == "my-project"
