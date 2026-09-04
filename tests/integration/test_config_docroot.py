"""Integration tests for docroot in config file."""

from pathlib import Path

import pytest
import yaml

from mcp_guide.runtime import create_runtime, get_runtime
from tests.helpers import create_test_session


@pytest.mark.anyio
async def test_new_config_has_docroot(runtime, tmp_path):
    """Test new config file includes docroot field."""
    session = await create_test_session(runtime, "test-project")

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
async def test_blank_docroot_is_replaced_with_and_persists_the_default(runtime, tmp_path, configured_docroot):
    """An unusable docroot is normalised before it can resolve relative to the checkout."""
    config_file = tmp_path / "config.yaml"
    config = {"projects": {}, "feature_flags": {}}
    if configured_docroot is not None:
        config["docroot"] = configured_docroot
    config_file.write_text(yaml.dump(config))

    session = await create_test_session(runtime, "test-project")

    assert await get_runtime().get_docroot() == str(tmp_path / "docs")
    persisted = yaml.safe_load(config_file.read_text())["docroot"]
    assert persisted == str(tmp_path / "docs")
    assert Path(persisted).is_absolute()


@pytest.mark.anyio
async def test_config_manager_retains_its_effective_docroot_until_restart(tmp_path):
    """A running manager keeps its startup docroot after external config changes."""
    config_file = tmp_path / "config.yaml"
    initial_docroot = tmp_path / "initial-docs"
    updated_docroot = tmp_path / "updated-docs"
    config_file.write_text(yaml.dump({"docroot": str(initial_docroot), "projects": {}}))

    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))
    await runtime.start()
    try:
        assert await runtime.get_docroot() == str(initial_docroot)

        config_file.write_text(yaml.dump({"docroot": str(updated_docroot), "projects": {}}))
        await runtime.configuration_service()._on_external_change(str(config_file))

        assert await runtime.get_docroot() == str(initial_docroot)
    finally:
        await runtime.stop()

    restarted = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))
    await restarted.start()
    try:
        assert await restarted.get_docroot() == str(updated_docroot)
    finally:
        await restarted.stop()


@pytest.mark.anyio
async def test_filling_missing_docroot_does_not_unpack_templates(tmp_path):
    """Persisting a default docroot must not install the packaged template tree."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("projects: {}\n")

    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))
    await runtime.start()
    try:
        await runtime.get_docroot()
    finally:
        await runtime.stop()

    docs = tmp_path / "docs"
    assert not (docs / ".original.zip").exists()
    assert not (docs / "_commands").exists()


@pytest.mark.anyio
async def test_first_run_persists_supplied_docroot(tmp_path, monkeypatch):
    """First-run --docroot docs leaves the supplied value in config.yaml."""
    from mcp_guide.installer.core import ORIGINAL_ARCHIVE

    monkeypatch.chdir(tmp_path)
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path), docroot="docs")
    await runtime.start()
    try:
        assert await runtime.get_docroot() == "docs"
    finally:
        await runtime.stop()

    persisted = yaml.safe_load((tmp_path / "config.yaml").read_text())["docroot"]
    assert persisted == "docs"
    assert (tmp_path / "docs" / ORIGINAL_ARCHIVE).exists()


@pytest.mark.anyio
async def test_relative_docroot_resolver_returns_absolute_paths(tmp_path, monkeypatch):
    """A persisted relative docroot still yields host-absolute resolved paths."""
    from mcp_guide.discovery.files import discover_document_files

    monkeypatch.chdir(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "intro.md").write_text("hello\n", encoding="utf-8")
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path / "cfg"), docroot="docs")
    await runtime.start()
    try:
        assert await runtime.get_docroot() == "docs"
        resolver = await runtime.get_docroot_resolver()
        resolved = resolver("intro.md")
        assert resolved.is_absolute()
        assert resolved == (docs / "intro.md").resolve()
        found = await discover_document_files(resolver(""), ["*.md"])
        assert any(path.name == "intro.md" for path in (info.path for info in found))
    finally:
        await runtime.stop()


@pytest.mark.anyio
async def test_first_run_persists_tilde_and_env_docroot(tmp_path, monkeypatch):
    """CLI tilde and $VAR docroot values are written unchanged; the resolver expands them."""
    from mcp_guide.installer.core import ORIGINAL_ARCHIVE

    home = tmp_path / "home"
    env_docs = tmp_path / "from-var"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GUIDE_DOCS", str(env_docs))

    tilde_runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path / "tilde"), docroot="~/guide-docs")
    await tilde_runtime.start()
    try:
        assert await tilde_runtime.get_docroot() == "~/guide-docs"
        resolver = await tilde_runtime.get_docroot_resolver()
        resolved = resolver("intro.md")
        assert resolved.is_absolute()
        assert resolved == (home / "guide-docs" / "intro.md").resolve()
        assert (home / "guide-docs" / ORIGINAL_ARCHIVE).exists()
    finally:
        await tilde_runtime.stop()

    env_runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path / "env"), docroot="$GUIDE_DOCS")
    await env_runtime.start()
    try:
        assert await env_runtime.get_docroot() == "$GUIDE_DOCS"
        resolver = await env_runtime.get_docroot_resolver()
        resolved = resolver("intro.md")
        assert resolved.is_absolute()
        assert resolved == (env_docs / "intro.md").resolve()
        assert (env_docs / ORIGINAL_ARCHIVE).exists()
    finally:
        await env_runtime.stop()


@pytest.mark.anyio
async def test_relative_config_dir_persists_absolute_docroot(tmp_path, monkeypatch):
    """First-run install stores an absolute docroot even when config_dir is relative."""
    monkeypatch.chdir(tmp_path)
    relative_dir = Path("relative-config")
    relative_dir.mkdir()

    runtime = create_runtime(lambda _owner: object(), config_dir=str(relative_dir))
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
async def test_saving_project_preserves_docroot(runtime, tmp_path):
    """Test saving a project preserves existing docroot."""
    session = await create_test_session(runtime, "test-project")

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
async def test_docroot_with_tilde_preserved(runtime, tmp_path):
    """Test docroot with tilde is preserved."""
    session = await create_test_session(runtime, "test-project")

    # Create project
    await session.get_project()

    # Set docroot with tilde
    config_file = tmp_path / "config.yaml"
    content = config_file.read_text()
    data = yaml.safe_load(content)
    data["docroot"] = "~/my-docs"
    config_file.write_text(yaml.dump(data))

    # Create another project
    session2 = await create_test_session(runtime, "another-project")
    await session2.get_project()

    # Verify tilde path preserved
    content = config_file.read_text()
    data = yaml.safe_load(content)
    assert data["docroot"] == "~/my-docs"


@pytest.mark.anyio
async def test_docroot_with_env_var_preserved(runtime, tmp_path):
    """Test docroot with environment variable is preserved."""
    session = await create_test_session(runtime, "test-project")

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
