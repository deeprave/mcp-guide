"""Tests for CLI script."""

import tomllib
from importlib import import_module
from pathlib import Path

import pytest
from click.testing import CliRunner


def use_minimal_templates(monkeypatch, tmp_path: Path) -> Path:
    """Replace the package template tree with a tiny synthetic set for tests."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "example.md").write_text("# Example\n")
    (templates_dir / "nested").mkdir()
    (templates_dir / "nested" / "guide.mustache").write_text("Guide content\n")

    async def fake_get_templates_path() -> Path:
        return templates_dir

    monkeypatch.setattr("mcp_guide.installer.core.get_templates_path", fake_get_templates_path)
    return templates_dir


class TestArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_parse_docroot_option(self) -> None:
        """Test that CLI accepts -d/--docroot option."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(
            cli, ["install", "--docroot", "/custom/path", "--configdir", "/custom/config", "--dry-run"]
        )

        # Assert
        assert result.exit_code == 0
        assert "Would use docroot: /custom/path" in result.output
        assert "Would use configdir: /custom/config" in result.output

    def test_mcp_install_entry_point_is_declared_and_runnable(self) -> None:
        """Test that the console script mapping exists and targets a runnable command.

        This keeps coverage on the packaging entry-point declaration without paying for a
        full throwaway virtualenv install on every test run.
        """
        project_root = Path(__file__).resolve().parents[3]
        pyproject = tomllib.loads((project_root / "pyproject.toml").read_text())

        scripts = pyproject["project"]["scripts"]
        target = scripts["mcp-install"]
        assert target == "mcp_guide.scripts.mcp_guide_install:cli"

        module_name, attr_name = target.split(":", maxsplit=1)
        command = getattr(import_module(module_name), attr_name)

        runner = CliRunner()
        result = runner.invoke(command, ["--help"])

        assert result.exit_code == 0

    @pytest.mark.e2e
    def test_installed_entry_point_help_runs(self, tmp_path: Path) -> None:
        """Installed console script should run from an isolated uv-synced virtualenv."""
        import os
        import subprocess
        import sys

        venv_dir = tmp_path / "venv"
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")

        project_root = Path(__file__).resolve().parents[3]
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(venv_dir)
        env["PATH"] = os.pathsep.join([str(bin_dir), env.get("PATH", "")])

        try:
            subprocess.check_call(
                ["uv", "sync", "--project", str(project_root), "--active", "--frozen", "--offline"],
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            pytest.skip(f"uv sync could not complete offline: {exc}")
        subprocess.check_call([str(bin_dir / "mcp-install"), "--help"], env=env)


class TestInstallation:
    """Tests for installation logic."""

    def test_install_creates_templates_and_config(self, tmp_path: Path, monkeypatch) -> None:
        """Test that install creates templates and config file."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # Act
        result = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert docroot.exists()
        assert (configdir / "config.yaml").exists()
        assert (docroot / ".original.zip").is_file()
        assert (docroot / "example.md").read_text() == "# Example\n"
        assert (docroot / "nested" / "guide.mustache").read_text() == "Guide content\n"
        assert "Enter docroot" not in result.output

    def test_install_resolves_tilde_docroot_and_persists_it_as_written(self, tmp_path: Path, monkeypatch) -> None:
        """A ``~/...`` --docroot is used via LazyPath.resolve() and stored unchanged."""
        import yaml

        from mcp_guide.installer.core import ORIGINAL_ARCHIVE
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        home = tmp_path / "home"
        configdir = tmp_path / "config"
        monkeypatch.setenv("HOME", str(home))
        use_minimal_templates(monkeypatch, tmp_path)

        result = runner.invoke(cli, ["install", "--docroot", "~/guide-docs", "--configdir", str(configdir)])

        assert result.exit_code == 0
        assert (home / "guide-docs" / ORIGINAL_ARCHIVE).exists()
        persisted = yaml.safe_load((configdir / "config.yaml").read_text(encoding="utf-8"))["docroot"]
        assert persisted == "~/guide-docs"


class TestEndToEndInstallation:
    """End-to-end tests for install command with smart update strategy."""

    def test_second_install_skips_unchanged_files(self, tmp_path: Path, monkeypatch) -> None:
        """Test that second install does not modify already-installed files (by content hash)."""
        # Arrange
        import hashlib

        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # First install
        result1 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])
        assert result1.exit_code == 0

        # Record hashes of all installed files (excluding the original archive)
        installed_files = [p for p in docroot.rglob("*") if p.is_file() and p.name != ".original.zip"]
        assert installed_files, "expected first install to produce at least one file"

        def file_hash(path: Path) -> str:
            h = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()

        first_hashes = {p.relative_to(docroot): file_hash(p) for p in installed_files}

        # Second install
        result2 = runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])
        assert result2.exit_code == 0

        # Recompute hashes and make sure nothing was changed
        installed_files_after = [p for p in docroot.rglob("*") if p.is_file() and p.name != ".original.zip"]
        second_hashes = {p.relative_to(docroot): file_hash(p) for p in installed_files_after}

        assert first_hashes == second_hashes

    def test_install_preserves_user_modifications_via_patch(self, tmp_path: Path, monkeypatch) -> None:
        """Test that install preserves user modifications when templates haven't changed."""
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

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


class TestInteractiveMode:
    """Tests for interactive mode."""

    @pytest.mark.parametrize(
        "flag",
        ["--interactive", "--quiet", "--verbose"],
    )
    def test_parse_mode_flags(self, flag: str) -> None:
        """Test that CLI accepts mode flags (-i/--interactive, -q/--quiet, -v/--verbose)."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["install", flag, "--dry-run"])

        # Assert
        assert result.exit_code == 0


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_suppresses_statistics(self, tmp_path: Path, monkeypatch) -> None:
        """Test that --quiet suppresses statistics output."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

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

    def test_prompts_for_docroot_in_interactive_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test that interactive mode prompts for docroot."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # Act - provide input for prompts
        result = runner.invoke(
            cli, ["install", "--interactive", "--configdir", str(configdir)], input=f"{docroot}\ny\n"
        )

        # Assert
        assert result.exit_code == 0
        assert docroot.exists()

    def test_displays_progress_in_verbose_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Test that verbose mode enables DEBUG logging."""
        # Arrange
        import logging

        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # Act
        result = runner.invoke(cli, ["install", "--verbose", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        # Verbose mode should configure the installer logger at DEBUG level
        installer_logger = logging.getLogger("mcp_guide.installer")
        # The logger should have been configured (has handlers and appropriate level)
        assert installer_logger.handlers, "Expected installer logger to have handlers in verbose mode"
        # At least one handler should be at DEBUG level or the logger itself
        has_debug = installer_logger.level == logging.DEBUG or any(
            h.level == logging.DEBUG for h in installer_logger.handlers
        )
        assert has_debug, "Expected DEBUG level logging in verbose mode"


class TestErrorHandling:
    """Tests for error handling."""

    def test_handles_permission_errors(self, tmp_path: Path, monkeypatch) -> None:
        """Test that permission errors are handled gracefully."""
        # Arrange
        import mcp_guide.installer.core
        from mcp_guide.scripts.mcp_guide_install import cli

        # Deterministic unavailable-installation boundary; OS permissions vary by test user.
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

        # Deterministic unavailable-installation boundary; OS permissions vary by test user.
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

    def test_update_command_uses_configured_docroot(self, tmp_path: Path, monkeypatch) -> None:
        """Test that update command uses docroot from config."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # First install
        runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        test_file = docroot / "example.md"
        test_file.write_text("# Example\nUser modified content\n")

        # Act - update without specifying docroot
        result = runner.invoke(cli, ["update", "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        # Check for completion message (statistics are now in logs)
        assert test_file.read_text() == "# Example\nUser modified content\n"
        from mcp_guide import __version__

        assert (docroot / ".version").read_text() == __version__

    def test_update_command_updates_config_when_docroot_specified(self, tmp_path: Path, monkeypatch) -> None:
        """Test that update command updates config when -d specified."""
        # Arrange
        import asyncio

        import yaml
        from anyio import Path as AsyncPath

        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        old_docroot = tmp_path / "old_docs"
        new_docroot = tmp_path / "new_docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # First install
        runner.invoke(cli, ["install", "--docroot", str(old_docroot), "--configdir", str(configdir)])

        # Act - update with new docroot
        result = runner.invoke(cli, ["update", "--docroot", str(new_docroot), "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        config_file = configdir / "config.yaml"

        async def read_config() -> dict[str, str]:
            content = await AsyncPath(config_file).read_text(encoding="utf-8")
            return yaml.safe_load(content)

        config = asyncio.run(read_config())
        assert config["docroot"] == str(new_docroot)


class TestStatusCommand:
    """Tests for status command."""

    def test_status_command_shows_installation_info(self, tmp_path: Path, monkeypatch) -> None:
        """Test that status command shows installation information."""
        # Arrange
        from mcp_guide.scripts.mcp_guide_install import cli

        runner = CliRunner()
        docroot = tmp_path / "docs"
        configdir = tmp_path / "config"
        use_minimal_templates(monkeypatch, tmp_path)

        # First install
        runner.invoke(cli, ["install", "--docroot", str(docroot), "--configdir", str(configdir)])

        # Act
        result = runner.invoke(cli, ["status", "--configdir", str(configdir)])

        # Assert
        assert result.exit_code == 0
        assert str(docroot) in result.output
        assert "config.yaml" in result.output
