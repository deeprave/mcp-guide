"""Tests for installer integration."""

from pathlib import Path

import pytest


class TestInstallAndCreateConfig:
    """Tests for install_and_create_config function."""

    @pytest.fixture
    def synthetic_templates(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Provide a minimal template source owned entirely by this test."""
        templates = tmp_path / "templates"
        commands = templates / "_commands"
        commands.mkdir(parents=True)
        (commands / "example.mustache").write_text("Example command\n")

        async def get_synthetic_templates() -> Path:
            return templates

        monkeypatch.setattr("mcp_guide.installer.core.get_templates_path", get_synthetic_templates)
        return templates

    @pytest.mark.anyio
    async def test_install_and_create_config_persists_supplied_docroot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_templates: Path
    ) -> None:
        """Resolve a supplied docroot for install only; persist the given value."""
        import yaml

        from mcp_guide.installer.core import ORIGINAL_ARCHIVE
        from mcp_guide.installer.integration import install_and_create_config

        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config" / "config.yaml"

        await install_and_create_config(config_file, Path("docs"))

        data = yaml.safe_load(config_file.read_text())
        assert data["docroot"] == "docs"
        assert (tmp_path / "docs" / ORIGINAL_ARCHIVE).exists()

    @pytest.mark.anyio
    async def test_install_and_create_config_persists_tilde_and_env_docroot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_templates: Path
    ) -> None:
        """Persist ~/ and $VAR docroot strings; expand only for the install tree."""
        import yaml

        from mcp_guide.installer.core import ORIGINAL_ARCHIVE
        from mcp_guide.installer.integration import install_and_create_config

        home = tmp_path / "home"
        env_docs = tmp_path / "from-var"
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("GUIDE_DOCS", str(env_docs))

        tilde_config = tmp_path / "tilde" / "config.yaml"
        await install_and_create_config(tilde_config, "~/guide-docs")
        assert yaml.safe_load(tilde_config.read_text())["docroot"] == "~/guide-docs"
        assert (home / "guide-docs" / ORIGINAL_ARCHIVE).exists()

        env_config = tmp_path / "env" / "config.yaml"
        await install_and_create_config(env_config, "$GUIDE_DOCS")
        assert yaml.safe_load(env_config.read_text())["docroot"] == "$GUIDE_DOCS"
        assert (env_docs / ORIGINAL_ARCHIVE).exists()

    @pytest.mark.anyio
    async def test_install_and_create_config_round_trips_yaml_special_docroot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_templates: Path
    ) -> None:
        """Persist YAML-significant docroot strings so later loads keep them as written."""
        import yaml

        from mcp_guide.installer.integration import install_and_create_config

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path / "home"))

        for index, docroot in enumerate(("~/My Docs: v2", "docs #1", "*docs", "&anchor")):
            config_file = tmp_path / f"cfg-{index}" / "config.yaml"
            await install_and_create_config(config_file, docroot)
            assert yaml.safe_load(config_file.read_text())["docroot"] == docroot
