"""Integration tests for docroot in config file."""

from pathlib import Path

import pytest
import yaml

from tests.helpers import create_test_session


@pytest.mark.anyio
async def test_new_config_has_docroot(tmp_path):
    """Test new config file includes docroot field."""
    session = await create_test_session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create a project to trigger config file creation
    await session.get_project()

    # Read config file
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)

    assert "docroot" in data
    assert "projects" in data
    assert Path(data["docroot"]).is_absolute()


@pytest.mark.anyio
@pytest.mark.parametrize("configured_docroot", [None, "", "   "], ids=["absent", "empty", "whitespace"])
async def test_blank_docroot_is_replaced_with_and_persists_the_default(tmp_path, configured_docroot):
    """An unusable docroot is normalised before it can resolve relative to the checkout."""
    config_file = tmp_path / "config.yaml"
    config = {"projects": {}, "feature_flags": {}}
    if configured_docroot is not None:
        config["docroot"] = configured_docroot
    config_file.write_text(yaml.dump(config))

    session = await create_test_session("test-project", _config_dir_for_tests=str(tmp_path))

    assert await session.runtime.get_docroot() == str(tmp_path / "docs")
    persisted = yaml.safe_load(config_file.read_text())["docroot"]
    assert persisted == str(tmp_path / "docs")
    assert Path(persisted).is_absolute()


@pytest.mark.anyio
async def test_config_manager_retains_its_effective_docroot_until_restart(tmp_path):
    """A running manager keeps its startup docroot after external config changes."""
    from mcp_guide.runtime import GuideRuntime

    config_file = tmp_path / "config.yaml"
    initial_docroot = tmp_path / "initial-docs"
    updated_docroot = tmp_path / "updated-docs"
    config_file.write_text(yaml.dump({"docroot": str(initial_docroot), "projects": {}}))

    runtime = GuideRuntime(lambda _owner: object(), config_dir=str(tmp_path))
    await runtime.start()
    try:
        assert await runtime.get_docroot() == str(initial_docroot)

        config_file.write_text(yaml.dump({"docroot": str(updated_docroot), "projects": {}}))
        await runtime.configuration_service()._on_external_change(str(config_file))

        assert await runtime.get_docroot() == str(initial_docroot)
    finally:
        await runtime.stop()

    restarted = GuideRuntime(lambda _owner: object(), config_dir=str(tmp_path))
    await restarted.start()
    try:
        assert await restarted.get_docroot() == str(updated_docroot)
    finally:
        await restarted.stop()


@pytest.mark.anyio
async def test_filling_missing_docroot_does_not_unpack_templates(tmp_path):
    """Persisting a default docroot must not install the packaged template tree."""
    from mcp_guide.runtime import GuideRuntime

    config_file = tmp_path / "config.yaml"
    config_file.write_text("projects: {}\n")

    runtime = GuideRuntime(lambda _owner: object(), config_dir=str(tmp_path))
    await runtime.start()
    try:
        await runtime.get_docroot()
    finally:
        await runtime.stop()

    docs = tmp_path / "docs"
    assert not (docs / ".original.zip").exists()
    assert not (docs / "_commands").exists()


@pytest.mark.anyio
async def test_relative_config_dir_persists_absolute_docroot(tmp_path, monkeypatch):
    """First-run install stores an absolute docroot even when config_dir is relative."""
    from mcp_guide.runtime import GuideRuntime

    monkeypatch.chdir(tmp_path)
    relative_dir = Path("relative-config")
    relative_dir.mkdir()

    runtime = GuideRuntime(lambda _owner: object(), config_dir=str(relative_dir))
    await runtime.start()
    try:
        docroot = await runtime.get_docroot()
    finally:
        await runtime.stop()

    data = yaml.safe_load((relative_dir / "config.yaml").read_text())
    persisted = Path(data["docroot"])
    expected = (tmp_path / "relative-config" / "docs").resolve()
    assert persisted.is_absolute()
    assert Path(docroot).is_absolute()
    assert persisted == expected
    assert persisted == Path(docroot)


@pytest.mark.anyio
async def test_saving_project_preserves_docroot(tmp_path):
    """Test saving a project preserves existing docroot."""
    session = await create_test_session("test-project", _config_dir_for_tests=str(tmp_path))

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


@pytest.mark.anyio
async def test_docroot_with_tilde_preserved(tmp_path):
    """Test docroot with tilde is preserved."""
    session = await create_test_session("test-project", _config_dir_for_tests=str(tmp_path))

    # Create project
    await session.get_project()

    # Set docroot with tilde
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/my-docs"
    config_file.write_text(yaml.dump(data))

    # Create another project
    session2 = await create_test_session("another-project", _config_dir_for_tests=str(tmp_path))
    await session2.get_project()

    # Verify tilde path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/my-docs"


@pytest.mark.anyio
async def test_docroot_with_env_var_preserved(tmp_path):
    """Test docroot with environment variable is preserved."""
    session = await create_test_session("test-project", _config_dir_for_tests=str(tmp_path))

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
