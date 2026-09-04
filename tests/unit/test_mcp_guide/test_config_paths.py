"""Tests for configuration path helpers."""

from pathlib import Path

import pytest

from mcp_guide.config_paths import clear_config_overrides, get_config_dir, get_docroot, get_documents_db, set_docroot


@pytest.mark.anyio
async def test_get_docroot_resolves_default_user_anchored_config_dir(tmp_path, monkeypatch):
    """The default docs location is resolved when used, not left as ``~/...``."""
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.chdir(workspace)
    clear_config_overrides()

    assert get_config_dir() == Path("~") / ".config" / "mcp-guide"
    assert get_docroot() == (home / ".config" / "mcp-guide" / "docs").resolve()
    assert get_documents_db() == Path("~") / ".config" / "mcp-guide" / "documents.db"


@pytest.mark.anyio
async def test_get_docroot_resolves_parent_references_in_override(tmp_path, monkeypatch):
    """An override is resolved, not merely expanded, before it is used."""
    home = tmp_path / "home"
    (home / "docs").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    set_docroot("~/docs/../docs")

    assert get_docroot() == (home / "docs").resolve()
    clear_config_overrides()
