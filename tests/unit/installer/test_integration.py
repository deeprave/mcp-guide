"""Tests for installer integration."""

from pathlib import Path

import pytest


class TestInstallAndCreateConfig:
    """Tests for install_and_create_config function."""

    @pytest.mark.anyio
    async def test_install_and_create_config_creates_templates_and_config(self, tmp_path: Path) -> None:
        """Test that install_and_create_config creates templates and config file."""
        # Arrange
        from mcp_guide.installer.integration import install_and_create_config

        config_file = tmp_path / "config" / "config.yaml"

        # Act
        await install_and_create_config(config_file)

        # Assert
        assert config_file.exists()
        content = config_file.read_text()
        assert "docroot:" in content
        assert "projects:" in content

    @pytest.mark.anyio
    async def test_install_and_create_config_installs_templates(self, tmp_path: Path) -> None:
        """Test that install_and_create_config installs template files."""
        # Arrange
        from mcp_guide.installer.integration import install_and_create_config

        config_file = tmp_path / "config" / "config.yaml"

        # Act
        await install_and_create_config(config_file)

        # Assert
        # Read docroot from config
        content = config_file.read_text()
        import yaml

        data = yaml.safe_load(content)
        docroot = Path(data["docroot"])

        # Check templates were installed
        assert docroot.exists()
        assert (docroot / "_commands").exists()

    @pytest.mark.anyio
    async def test_install_and_create_config_creates_archive(self, tmp_path: Path) -> None:
        """Test that install_and_create_config creates originals archive."""
        # Arrange
        from mcp_guide.installer.core import ORIGINAL_ARCHIVE
        from mcp_guide.installer.integration import install_and_create_config

        config_file = tmp_path / "config" / "config.yaml"

        # Act
        await install_and_create_config(config_file)

        # Assert
        # Read docroot from config
        content = config_file.read_text()
        import yaml

        data = yaml.safe_load(content)
        docroot = Path(data["docroot"])

        # Check archive was created
        archive_path = docroot / ORIGINAL_ARCHIVE
        assert archive_path.exists()

    @pytest.mark.anyio
    async def test_install_and_create_config_writes_version(self, tmp_path: Path) -> None:
        """Test that install_and_create_config writes version file."""
        # Arrange
        from mcp_guide.installer.core import VERSION_FILE
        from mcp_guide.installer.integration import install_and_create_config

        config_file = tmp_path / "config" / "config.yaml"

        # Act
        await install_and_create_config(config_file)

        # Assert
        # Read docroot from config
        content = config_file.read_text()
        import yaml

        data = yaml.safe_load(content)
        docroot = Path(data["docroot"])

        # Check version file was created
        version_path = docroot / VERSION_FILE
        assert version_path.exists()
        version = version_path.read_text().strip()
        assert len(version) > 0

    @pytest.mark.anyio
    async def test_install_and_create_config_persists_supplied_docroot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
