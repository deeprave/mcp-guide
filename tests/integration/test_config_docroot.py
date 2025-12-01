"""Integration tests for docroot in config file."""

import yaml

from mcp_guide.config import ConfigManager


async def test_new_config_has_docroot(tmp_path):
    """Test new config file includes docroot field."""
    config_dir = str(tmp_path)
    manager = ConfigManager(config_dir)

    # Create a project to trigger config file creation
    await manager.get_or_create_project_config("test-project")

    # Read config file
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)

    assert "docroot" in data
    assert "projects" in data
    assert data["docroot"]  # Should have a value


async def test_saving_project_preserves_docroot(tmp_path):
    """Test saving a project preserves existing docroot."""
    config_dir = str(tmp_path)
    manager = ConfigManager(config_dir)

    # Create initial project
    project = await manager.get_or_create_project_config("test-project")

    # Manually edit docroot in config file
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/custom-docs"
    config_file.write_text(yaml.dump(data))

    # Save project again
    await manager.save_project_config(project)

    # Verify docroot is preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/custom-docs"


async def test_docroot_with_tilde_preserved(tmp_path):
    """Test docroot with tilde is preserved."""
    config_dir = str(tmp_path)
    manager = ConfigManager(config_dir)

    # Create project
    await manager.get_or_create_project_config("test-project")

    # Set docroot with tilde
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/my-docs"
    config_file.write_text(yaml.dump(data))

    # Create another project
    await manager.get_or_create_project_config("another-project")

    # Verify tilde path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/my-docs"


async def test_docroot_with_env_var_preserved(tmp_path):
    """Test docroot with environment variable is preserved."""
    config_dir = str(tmp_path)
    manager = ConfigManager(config_dir)

    # Create project
    await manager.get_or_create_project_config("test-project")

    # Set docroot with env var
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "${HOME}/docs"
    config_file.write_text(yaml.dump(data))

    # Delete project
    await manager.delete_project("test-project")

    # Verify env var path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "${HOME}/docs"
