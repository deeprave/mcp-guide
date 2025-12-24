"""Tests for configuration migration logic."""

import tempfile
from pathlib import Path

import pytest
import yaml

from mcp_guide.config import ConfigManager


class TestConfigMigration:
    """Test configuration migration from legacy to hash-based format."""

    @pytest.mark.asyncio
    async def test_migration_detection_legacy_format(self):
        """Migration is detected for legacy format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_manager = ConfigManager(config_dir=tmp_dir)

            # Create legacy format data
            legacy_data = {
                "my-project": {"categories": {}, "collections": {}},
                "other-project": {"categories": {}, "collections": {}},
            }

            needs_migration = config_manager._needs_migration(legacy_data)
            assert needs_migration is True

    @pytest.mark.asyncio
    async def test_migration_detection_new_format(self):
        """Migration is not needed for new format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_manager = ConfigManager(config_dir=tmp_dir)

            # Create new format data
            new_data = {"my-project-abcdef12": {"hash": "abcdef1234567890" * 4, "categories": {}, "collections": {}}}

            needs_migration = config_manager._needs_migration(new_data)
            assert needs_migration is False

    @pytest.mark.asyncio
    async def test_project_migration(self):
        """Projects are migrated correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_manager = ConfigManager(config_dir=tmp_dir)
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create legacy format data
            legacy_data = {
                "my-project": {
                    "categories": {"docs": {"dir": "docs", "patterns": ["*.md"]}},
                    "collections": {"all": {"categories": ["docs"]}},
                }
            }

            migrated_data = await config_manager._migrate_projects(legacy_data, config_file)

            # Check migration results
            assert len(migrated_data) == 1

            # Find the migrated project
            migrated_key = list(migrated_data.keys())[0]
            migrated_project = migrated_data[migrated_key]

            # Verify key format
            assert migrated_key.startswith("my-project-")
            assert len(migrated_key.split("-")[-1]) == 8  # Short hash

            # Verify data preservation
            assert migrated_project["hash"] is not None
            assert len(migrated_project["hash"]) == 64  # Full SHA256
            assert migrated_project["categories"] == legacy_data["my-project"]["categories"]
            assert migrated_project["collections"] == legacy_data["my-project"]["collections"]

    @pytest.mark.asyncio
    async def test_full_migration_workflow(self):
        """Full migration workflow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create the config file with the expected name
            from mcp_guide.config_paths import get_config_file

            config_file = get_config_file(tmp_dir)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Create legacy config file
            legacy_config = {
                "docroot": str(tmp_dir),
                "projects": {
                    "test-project": {
                        "categories": {"docs": {"dir": "docs", "patterns": ["*.md"]}},
                        "collections": {"all": {"categories": ["docs"]}},
                    }
                },
            }

            config_file.write_text(yaml.dump(legacy_config))

            # Load through ConfigManager (should trigger migration)
            config_manager = ConfigManager(config_dir=tmp_dir)
            projects = await config_manager.get_all_project_configs()

            # Verify migration occurred
            assert len(projects) == 1
            project = list(projects.values())[0]

            assert project.name == "test-project"
            assert project.hash is not None
            assert len(project.hash) == 64

            # Verify config file was updated
            updated_config = yaml.safe_load(config_file.read_text())
            updated_projects = updated_config["projects"]

            # Should have hash-suffixed key
            project_keys = list(updated_projects.keys())
            assert len(project_keys) == 1
            assert project_keys[0].startswith("test-project-")
            assert len(project_keys[0].split("-")[-1]) == 8

    @pytest.mark.asyncio
    async def test_migration_preserves_all_data(self):
        """Migration preserves all project data fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_manager = ConfigManager(config_dir=tmp_dir)
            config_file = Path(tmp_dir) / "guide.yaml"

            # Create comprehensive legacy data
            legacy_data = {
                "complex-project": {
                    "categories": {
                        "docs": {"dir": "documentation", "patterns": ["*.md", "*.rst"]},
                        "examples": {"dir": "examples", "patterns": ["*.py"]},
                    },
                    "collections": {"all": {"categories": ["docs", "examples"]}, "docs-only": {"categories": ["docs"]}},
                    "project_flags": {"feature_x": True, "debug_mode": False},
                }
            }

            migrated_data = await config_manager._migrate_projects(legacy_data, config_file)
            migrated_project = list(migrated_data.values())[0]

            # Verify all fields preserved (except timestamps which are ignored)
            original = legacy_data["complex-project"]
            assert migrated_project["categories"] == original["categories"]
            assert migrated_project["collections"] == original["collections"]
            assert migrated_project["project_flags"] == original["project_flags"]

            # Timestamp fields should not be present in migrated data
            assert "created_at" not in migrated_project
            assert "updated_at" not in migrated_project

            # Plus new hash field
            assert "hash" in migrated_project
            assert len(migrated_project["hash"]) == 64
