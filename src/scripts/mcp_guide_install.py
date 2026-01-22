#!/usr/bin/env python
"""MCP Guide installer script."""

import asyncio
from pathlib import Path

import click
import yaml


@click.command()
@click.argument("command", type=click.Choice(["install", "update", "status", "list"]), default="install")
@click.option("-d", "--docroot", type=click.Path(), help="Custom docroot path")
@click.option("-c", "--configdir", type=click.Path(), help="Custom config directory")
@click.option("-i", "--interactive", is_flag=True, help="Enable interactive prompts")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
def cli(
    command: str, docroot: str | None, configdir: str | None, interactive: bool, verbose: bool, dry_run: bool
) -> None:
    """Install or update MCP Guide templates.

    Commands:
      install  Install templates (default)
      update   Update existing installation
      status   Show installation status
      list     List installed files
    """
    if dry_run:
        click.echo(f"Dry run mode - {command} - no changes will be made")
        if interactive:
            click.echo("Interactive mode enabled")
        if verbose:
            click.echo("Verbose mode enabled")
        if docroot:
            click.echo(f"Would use docroot: {docroot}")
        if configdir:
            click.echo(f"Would use configdir: {configdir}")
        return

    asyncio.run(main(command, docroot, configdir, interactive, verbose))


async def main(command: str, docroot: str | None, configdir: str | None, interactive: bool, verbose: bool) -> None:
    """Main installation logic."""
    import aiofiles

    from mcp_guide import __version__
    from mcp_guide.config_paths import get_config_dir, get_docroot
    from mcp_guide.installer.core import (
        ORIGINAL_ARCHIVE,
        install_templates,
        read_version,
        update_templates,
        write_version,
    )
    from mcp_guide.installer.integration import install_and_create_config

    try:
        # Resolve config directory and file
        configdir_path = Path(configdir) if configdir else get_config_dir()
        config_file = configdir_path / "config.yaml"
        default_docroot = get_docroot(str(configdir_path))

        # For update/status/list, read existing config
        if command in ("update", "status", "list"):
            if not config_file.exists():
                click.echo("Error: No installation found. Run 'mcp-install install' first.", err=True)
                raise SystemExit(1)

            # Read docroot from config
            async with aiofiles.open(config_file, encoding="utf-8") as f:
                config_content = await f.read()
            config = yaml.safe_load(config_content)
            docroot_path = Path(docroot) if docroot else Path(config["docroot"])
        else:
            # For install, use provided or default docroot
            docroot_path = Path(docroot) if docroot else default_docroot

        # Interactive prompts
        custom_docroot = docroot is not None
        if interactive:
            if command == "install" and not docroot:
                docroot_input = click.prompt("Enter docroot path", default=str(docroot_path))
                docroot_path = Path(docroot_input)
                # Mark as custom if user changed it
                custom_docroot = str(docroot_path) != str(default_docroot)

            if not click.confirm(f"{command.capitalize()} templates to {docroot_path}?", default=True):
                click.echo(f"{command.capitalize()} cancelled")
                return

        if verbose:
            click.echo(f"{command.capitalize()}ing to: {docroot_path}")
            click.echo(f"Config file: {config_file}")

        archive_path = docroot_path / ORIGINAL_ARCHIVE

        # Execute command
        if command == "install":
            if verbose:
                click.echo("Installing templates...")

            if config_file.exists() and not custom_docroot:
                # Config exists, just install templates
                result = await install_templates(docroot_path, archive_path)
                await write_version(docroot_path, __version__)
                click.echo(f"Installed {result['files_installed']} files to {docroot_path}")
            else:
                # Use integration function for first install or custom docroot
                await install_and_create_config(config_file, docroot_path if custom_docroot else None)
                click.echo(f"Installed templates to {docroot_path}")

            click.echo(f"Config saved to {config_file}")

        elif command == "update":
            if verbose:
                click.echo("Updating templates...")

            result = await update_templates(docroot_path, archive_path)
            await write_version(docroot_path, __version__)

            # Update config if docroot changed
            if custom_docroot:
                async with aiofiles.open(config_file, encoding="utf-8") as f:
                    config_content = await f.read()
                config = yaml.safe_load(config_content) or {}
                config["docroot"] = str(docroot_path)
                async with aiofiles.open(config_file, "w", encoding="utf-8") as f:
                    await f.write(yaml.safe_dump(config))

            click.echo(f"Processed {result['files_processed']} files")
            click.echo(f"  Skipped: {result['skipped']}")
            click.echo(f"  Replaced: {result['replaced']}")
            click.echo(f"  Patched: {result['patched']}")
            if result["conflict"] > 0:
                click.echo(f"  Conflicts: {result['conflict']} (backups created)")

        elif command == "status":
            installed_version = await read_version(docroot_path)
            click.echo(f"Installation found at: {docroot_path}")
            click.echo(f"Config: {config_file}")
            click.echo(f"Archive: {archive_path}")
            click.echo(f"Installed version: {installed_version or 'unknown'}")
            click.echo(f"Current version: {__version__}")
            if installed_version and installed_version != __version__:
                click.echo("⚠️  Update available")

        elif command == "list":
            if not docroot_path.exists():
                click.echo("No installation found")
                return

            template_files = sorted(docroot_path.rglob("*.mustache"))
            click.echo(f"Installed files ({len(template_files)}):")
            for template_file in template_files[:20]:
                click.echo(f"  {template_file.relative_to(docroot_path)}")
            if len(template_files) > 20:
                click.echo(f"  ... and {len(template_files) - 20} more")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except PermissionError as e:
        click.echo(f"Permission denied: {e}", err=True)
        raise SystemExit(1)
    except FileNotFoundError as e:
        click.echo(f"File not found: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise


if __name__ == "__main__":
    cli()
