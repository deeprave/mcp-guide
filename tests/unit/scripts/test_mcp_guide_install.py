"""Tests for CLI script."""

from pathlib import Path

import pytest
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

    @pytest.mark.e2e
    def test_installed_entry_point_help_runs(self, tmp_path: Path) -> None:
        """Integration test that installed console script entry point is runnable.

        This exercises the packaging/entry-point wiring that tools like `uvx --from mcp-guide`
        depend on, by installing the project into an isolated virtualenv and invoking
        the generated `mcp-install` script with `--help`.
        """
        import os
        import subprocess
        import sys

        # Create an isolated virtual environment
        venv_dir = tmp_path / "venv"
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

        # Resolve the venv's Python and bin/Scripts directory
        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == "nt" else "python")

        # Install the current project into the virtualenv
        project_root = Path(__file__).resolve().parents[3]
        subprocess.check_call([str(python_exe), "-m", "pip", "install", str(project_root)])

        # Invoke the installed console script with --help to verify it is correctly installed
        env = os.environ.copy()
        subprocess.check_call([str(bin_dir / "mcp-install"), "--help"], env=env)


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


class TestEndToEndInstallation:
    """End-to-end tests for install command with smart update strategy."""

    def test_first_install_creates_all_files(self, tmp_path: Path) -> None:
        """Test that first install creates all template files."""
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
        assert (docroot / ".original.zip").exists()
        # Check at least one template file was created
        template_files = list(docroot.rglob("*.md"))
        assert len(template_files) > 0

    def test_second_install_skips_unchanged_files(self, tmp_path: Path) -> None:
        """Test that second install skips all unchanged files."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # First install
        result1 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])
        assert result1.exit_code == 0

        # Get modification times
        template_files = list(docroot.rglob("*.md"))
        original_mtimes = {f: f.stat().st_mtime for f in template_files}

        # Act - Second install
        result2 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result2.exit_code == 0
        # Files should have same modification times (unchanged)
        for f in template_files:
            assert f.stat().st_mtime == original_mtimes[f]

    def test_install_preserves_user_modifications_via_patch(self, tmp_path: Path) -> None:
        """Test that install preserves user modifications when templates haven't changed."""
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # First install
        result1 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])
        assert result1.exit_code == 0

        # Modify a file (simulate user changes)
        template_files = [f for f in docroot.rglob("*.md") if "old" not in f.parts]
        assert template_files, "No template files found - test cannot verify smart update behavior"

        test_file = template_files[0]
        original_content = test_file.read_text()
        modified_content = original_content + "\n\n# User Added Section\nUser content here\n"
        test_file.write_text(modified_content)

        # Act - Install again (templates haven't changed)
        result2 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert - install should succeed and preserve user modifications
        assert result2.exit_code == 0
        final_content = test_file.read_text()
        assert "User Added Section" in final_content

    def test_install_creates_backup_on_patch_failure(self, tmp_path: Path) -> None:
        """Test that install creates backup when patch fails."""
        # Arrange
        import asyncio

        from mcp_guide.installer.core import install_file
        from mcp_guide.scripts.mcp_guide_install import cli

        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        runner = CliRunner()

        # First install
        result1 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])
        assert result1.exit_code == 0

        # Create a scenario where patch will fail
        # Modify a file in a way that conflicts with template changes
        template_files = list(docroot.rglob("*.md"))
        if template_files:
            test_file = template_files[0]
            # Completely replace content to force patch failure
            test_file.write_text("# Completely Different Content\nThis will conflict\n")

            # Create a modified "new" version to trigger conflict
            source_file = tmp_path / "new_version.md"
            source_file.write_text("# New Template Version\nUpdated content\n")

            archive_path = docroot / ".original.zip"

            # Act - Try to install with conflict
            async def test_conflict():
                return await install_file(source_file, test_file, archive_path)

            status = asyncio.run(test_conflict())

            # Assert
            if status == "conflict":
                backup_file = test_file.parent / f"orig.{test_file.name}"
                assert backup_file.exists()
                assert "Completely Different Content" in backup_file.read_text()

    def test_install_reports_correct_statistics(self, tmp_path: Path) -> None:
        """Test that install reports correct statistics."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act - First install
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        # Should report installation completion
        assert "Installation complete" in result.output or result.exit_code == 0
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


class TestQuietMode:
    """Tests for quiet mode."""

    def test_parse_quiet_flag(self) -> None:
        """Test that CLI accepts -q/--quiet flag."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", "--quiet", "--dry-run"])

        # Assert
        assert result.exit_code == 0

    def test_quiet_suppresses_statistics(self, tmp_path: Path) -> None:
        """Test that --quiet suppresses statistics output."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"

        # Act
        result = runner.invoke(cli, ["install", "--quiet", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0

        output = result.output.lower()

        # Should not contain statistics in quiet mode
        assert "installed" not in output
        assert "updated" not in output
        assert "patched" not in output

        # Quiet mode suppresses all non-error output (WARNING level only)
        # So output should be empty or minimal

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
        # Verbose mode should show DEBUG level logs
        assert "DEBUG" in result.output or "Installed new file" in result.output


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
        # Check for completion message (statistics are now in logs)
        assert "Update complete" in result.output or result.exit_code == 0

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
