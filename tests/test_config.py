"""Tests for ConfigManager."""

import pytest

from mcp_guide.config import ConfigManager


class TestConfigManager:
    """Tests for ConfigManager."""

    @pytest.mark.asyncio
    async def test_singleton_pattern(self, tmp_path):
        """Module-level singleton should return same instance."""
        from mcp_guide.config import get_config_manager

        manager1 = await get_config_manager()
        manager2 = await get_config_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_config_file_initialization(self, tmp_path):
        """Config file should be initialized if it doesn't exist."""
        from mcp_guide.config import ConfigManager

        manager = ConfigManager(config_dir=str(tmp_path))
        await manager._ensure_initialized()
        assert manager.config_file.exists()

    @pytest.mark.asyncio
    async def test_get_or_create_project_config(self, tmp_path):
        """Should create new project if it doesn't exist."""
        manager = ConfigManager(config_dir=str(tmp_path))
        project = await manager.get_or_create_project_config("test-project")
        assert project.name == "test-project"
        assert len(project.categories) == 0

    @pytest.mark.asyncio
    async def test_get_existing_project_config(self, tmp_path):
        """Should return existing project."""
        manager = ConfigManager(config_dir=str(tmp_path))
        project1 = await manager.get_or_create_project_config("test-project")
        project2 = await manager.get_or_create_project_config("test-project")
        assert project1.name == project2.name

    @pytest.mark.asyncio
    async def test_save_project_config(self, tmp_path):
        """Should save project config to file."""
        from mcp_guide.models import Category

        manager = ConfigManager(config_dir=str(tmp_path))
        project = await manager.get_or_create_project_config("test-project")
        category = Category(dir="docs/", patterns=["*.md"])
        updated_project = project.with_category("docs", category)

        await manager.save_project_config(updated_project)

        # Reload and verify
        reloaded = await manager.get_or_create_project_config("test-project")
        assert len(reloaded.categories) == 1
        assert "docs" in reloaded.categories

    @pytest.mark.asyncio
    async def test_list_projects(self, tmp_path):
        """Should list all project names."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("project1")
        await manager.get_or_create_project_config("project2")

        projects = await manager.list_projects()
        assert "project1" in projects
        assert "project2" in projects
        assert len(projects) == 2

    @pytest.mark.asyncio
    async def test_rename_project(self, tmp_path):
        """Should rename a project."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("old-name")

        await manager.rename_project("old-name", "new-name")

        projects = await manager.list_projects()
        assert "new-name" in projects
        assert "old-name" not in projects

    @pytest.mark.asyncio
    async def test_rename_nonexistent_project(self, tmp_path):
        """Should raise error when renaming nonexistent project."""
        manager = ConfigManager(config_dir=str(tmp_path))

        with pytest.raises(ValueError, match="not found"):
            await manager.rename_project("nonexistent", "new-name")

    @pytest.mark.asyncio
    async def test_delete_project(self, tmp_path):
        """Should delete a project."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        await manager.delete_project("test-project")

        projects = await manager.list_projects()
        assert "test-project" not in projects

    @pytest.mark.asyncio
    async def test_delete_nonexistent_project(self, tmp_path):
        """Should raise error when deleting nonexistent project."""
        manager = ConfigManager(config_dir=str(tmp_path))

        with pytest.raises(ValueError, match="not found"):
            await manager.delete_project("nonexistent")

    @pytest.mark.asyncio
    async def test_corrupted_yaml_handling(self, tmp_path):
        """Should raise YAMLError with file location for corrupted YAML."""
        manager = ConfigManager(config_dir=str(tmp_path))

        # Initialize to create the config file
        await manager._ensure_initialized()

        # Corrupt the YAML file
        manager.config_file.write_text("projects: {invalid yaml content")

        with pytest.raises(Exception) as exc_info:
            await manager.list_projects()

        # Should be a YAML error with file path in message
        assert "yaml" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_project_name_validation(self, tmp_path):
        """Should validate project name before operations."""
        manager = ConfigManager(config_dir=str(tmp_path))

        # Test various invalid names
        with pytest.raises(ValueError, match="Invalid project name"):
            await manager.get_or_create_project_config("project@name")

        with pytest.raises(ValueError, match="Invalid project name"):
            await manager.get_or_create_project_config("project name")

        with pytest.raises(ValueError, match="cannot be empty"):
            await manager.get_or_create_project_config("")


class TestAllowedPathsSerialization:
    """Tests for allowed_paths serialization behavior."""

    @pytest.mark.asyncio
    async def test_default_allowed_paths_not_serialized(self, tmp_path):
        """allowed_paths should not be in YAML when using defaults."""
        manager = ConfigManager(config_dir=str(tmp_path))
        project = await manager.get_or_create_project_config("test")

        await manager.save_project_config(project)

        # Read raw YAML and parse it to check structure
        content = manager.config_file.read_text()
        import yaml

        config_data = yaml.safe_load(content)

        # Check that allowed_paths is not in the project data
        project_key = next(iter(config_data["projects"].keys()))
        project_data = config_data["projects"][project_key]
        assert "allowed_paths" not in project_data

    @pytest.mark.asyncio
    async def test_custom_allowed_paths_serialized(self, tmp_path):
        """allowed_paths should be in YAML when different from defaults."""
        from dataclasses import replace

        manager = ConfigManager(config_dir=str(tmp_path))
        project = await manager.get_or_create_project_config("test")
        project = replace(project, allowed_paths=["custom/"])

        await manager.save_project_config(project)

        # Read raw YAML and parse it to check structure
        content = manager.config_file.read_text()
        import yaml

        config_data = yaml.safe_load(content)

        # Check that allowed_paths is in the project data
        project_key = next(iter(config_data["projects"].keys()))
        project_data = config_data["projects"][project_key]
        assert "allowed_paths" in project_data
        assert project_data["allowed_paths"] == ["custom/"]
