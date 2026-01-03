"""Integration tests for docroot in config file."""

import yaml

from mcp_guide.session import Session


async def test_new_config_has_docroot(tmp_path):
    """Test new config file includes docroot field."""
    session = Session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create a project to trigger config file creation
    await session.get_project()

    # Read config file
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)

    assert "docroot" in data
    assert "projects" in data
    assert data["docroot"]  # Should have a value


async def test_saving_project_preserves_docroot(tmp_path):
    """Test saving a project preserves existing docroot."""
    session = Session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create initial project
    project = await session.get_project()

    # Manually edit docroot in config file
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/custom-docs"
    config_file.write_text(yaml.dump(data))

    # Save project again
    await session.update_config(lambda p: p)

    # Verify docroot is preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/custom-docs"


async def test_docroot_with_tilde_preserved(tmp_path):
    """Test docroot with tilde is preserved."""
    session = Session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create project
    await session.get_project()

    # Set docroot with tilde
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/my-docs"
    config_file.write_text(yaml.dump(data))

    # Create another project
    session2 = Session("another-project", _config_dir_for_tests=str(tmp_path))
    await session2.get_project()

    # Verify tilde path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/my-docs"


async def test_docroot_with_env_var_preserved(tmp_path):
    """Test docroot with environment variable is preserved."""
    session = Session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create project
    await session.get_project()

    # Set docroot with env var
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "${HOME}/docs"
    config_file.write_text(yaml.dump(data))

    # Update project to trigger save
    await session.update_config(lambda p: p)

    # Verify env var path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "${HOME}/docs"
