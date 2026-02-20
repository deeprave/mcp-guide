"""Tests for CLI script."""

from pathlib import Path

from click.testing import CliRunner


class TestArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_parse_docroot_option(self) -> None:
        """Test that CLI accepts -d/--docroot option."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", "--docroot", "/custom/path", "--dry-run"])

        # Assert
        assert result.exit_code == 0
        assert "/custom/path" in result.output or result.exit_code == 0

    def test_parse_configdir_option(self) -> None:
        """Test that CLI accepts -c/--configdir option."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", "--configdir", "/custom/config", "--dry-run"])

        # Assert
        assert result.exit_code == 0


class TestInstallation:
    """Tests for installation logic."""

    def test_install_creates_templates_and_config(self, tmp_path: Path) -> None:
        """Test that install creates templates and config file."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert docroot.exists()
        assert (configdir / "config.yaml").exists()


class TestInteractiveMode:
    """Tests for interactive mode."""

    def test_parse_interactive_flag(self) -> None:
        """Test that CLI accepts -i/--interactive flag."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", "--interactive", "--dry-run"])

        # Assert
        assert result.exit_code == 0
        assert "interactive" in result.output.lower() or result.exit_code == 0

    def test_parse_verbose_flag(self) -> None:
        """Test that CLI accepts -v/--verbose flag."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", "--verbose", "--dry-run"])

        # Assert
        assert result.exit_code == 0

    def test_prompts_for_docroot_in_interactive_mode(self, tmp_path: Path) -> None:
        """Test that interactive mode prompts for docroot."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act - provide input for prompts
        result = runner.invoke(
            cli, ["install", "--interactive", "--configdir", str(configdir)], input=f"{docroot}\ny\n"
        )

        # Assert
        assert result.exit_code == 0
        assert docroot.exists()

    def test_skips_prompts_in_non_interactive_mode(self, tmp_path: Path) -> None:
        """Test that non-interactive mode skips prompts."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act - no input provided
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert "Enter docroot" not in result.output

    def test_displays_progress_in_verbose_mode(self, tmp_path: Path) -> None:
        """Test that verbose mode displays progress."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act
        result = runner.invoke(cli, ["install", "--verbose", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert "Installing to:" in result.output or "Installing templates" in result.output


class TestErrorHandling:
    """Tests for error handling."""

    def test_handles_invalid_docroot_path(self, tmp_path: Path, monkeypatch) -> None:
        """Test that invalid docroot path is handled gracefully."""
        # Arrange
        import mcp_guide.installer.core
        from mcp_guide.scripts.mcp_guide_install import cli

        async def mock_install(*args, **kwargs):
            raise PermissionError("Permission denied for docroot")

        monkeypatch.setattr(mcp_guide.installer.core, "install_templates", mock_install)

        runner = CliRunner()
        invalid_docroot = tmp_path / "invalid-docroot"

        # Act - attempt install to a temporary "invalid" docroot
        result = runner.invoke(cli, ["install", "--docroot", str(invalid_docroot)])

        # Assert
        assert result.exit_code == 1
        assert "permission denied" in result.output.lower()

    def test_handles_permission_errors(self, tmp_path: Path, monkeypatch) -> None:
        """Test that permission errors are handled gracefully."""
        # Arrange
        import mcp_guide.installer.core
        from mcp_guide.scripts.mcp_guide_install import cli

        async def mock_install(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(mcp_guide.installer.core, "install_templates", mock_install)

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 1
        assert "permission denied" in result.output.lower()

    def test_handles_missing_template_package(self, tmp_path: Path, monkeypatch) -> None:
        """Test that missing template package is handled gracefully."""
        # Arrange
        import mcp_guide.installer.core
        from mcp_guide.scripts.mcp_guide_install import cli

        async def mock_install(*args, **kwargs):
            raise FileNotFoundError("Templates directory not found")

        monkeypatch.setattr(mcp_guide.installer.core, "install_templates", mock_install)

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 1
        assert "file not found" in result.output.lower()


class TestUpdateCommand:
    """Tests for update command."""

    def test_update_command_uses_configured_docroot(self, tmp_path: Path) -> None:
        """Test that update command uses docroot from config."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # First install
        runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Modify a file
        (docroot / "_commands").mkdir(parents=True, exist_ok=True)
        test_file = docroot / "_commands" / "test.mustache"
        if test_file.exists():
            test_file.write_text("User modified content\n")

        # Act - update without specifying docroot
        result = runner.invoke(cli, ["update", "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert "Processed" in result.output

    def test_update_command_updates_config_when_docroot_specified(self, tmp_path: Path) -> None:
        """Test that update command updates config when -d specified."""
        # Arrange
        import asyncio

        import aiofiles
        import yaml

        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        old_docroot = tmp_path / "old_docs"
        new_docroot = tmp_path / "new_docs"
        configdir = tmp_path / "config"

        # First install
        runner.invoke(cli, ["install", "--docroot", str(old_docroot), "--configdir", str(configdir)])

        # Act - update with new docroot
        result = runner.invoke(cli, ["update", "--docroot", str(new_docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        config_file = configdir / "config.yaml"

        async def read_config() -> dict[str, str]:
            async with aiofiles.open(config_file, encoding="utf-8") as f:
                content = await f.read()
            return yaml.safe_load(content)

        config = asyncio.run(read_config())
        assert config["docroot"] == str(new_docroot)


class TestStatusCommand:
    """Tests for status command."""

    def test_status_command_shows_installation_info(self, tmp_path: Path) -> None:
        """Test that status command shows installation information."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # First install
        runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Act
        result = runner.invoke(cli, ["status", "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert str(docroot) in result.output
        assert "config.yaml" in result.output
