"""Tests for installer integration."""

from pathlib import Path

import pytest


class TestInstallAndCreateConfig:
    """Tests for install_and_create_config function."""

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
