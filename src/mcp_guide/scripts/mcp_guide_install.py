#!/usr/bin/env python
"""MCP Guide installer script."""

import asyncio
import logging
from pathlib import Path

import click
import yaml


def setup_installer_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging for installer CLI.

    Args:
        verbose: Enable DEBUG level logging
        quiet: Enable WARNING level logging only
    """
    from mcp_guide.core.mcp_log import create_console_handler, create_formatter, get_log_level

    # Determine log level
    if verbose:
        level = "DEBUG"
    elif quiet:
        level = "WARNING"
    else:
        level = "INFO"

    # Create console handler with mcp-guide's formatter
    handler = create_console_handler()
    formatter = create_formatter(json_format=False)
    handler.setFormatter(formatter)
    handler.setLevel(get_log_level(level))

    # Configure installer logger (not root) to avoid impacting other loggers
    installer_logger = logging.getLogger("mcp_guide.installer")
    installer_logger.setLevel(get_log_level(level))

    # Remove any existing handlers to avoid duplicate log output when this
    # function is called multiple times in the same process.
    for existing_handler in list(installer_logger.handlers):
        installer_logger.removeHandler(existing_handler)

    installer_logger.addHandler(handler)
    # Prevent propagation to root logger to avoid duplicate output
    installer_logger.propagate = False


@click.command()
@click.argument("command", type=click.Choice(["install", "update", "status", "list"]), default="install")
@click.option("-d", "--docroot", type=click.Path(), help="Custom docroot path")
@click.option("-c", "--configdir", type=click.Path(), help="Custom config directory")
@click.option("-i", "--interactive", is_flag=True, help="Enable interactive prompts")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress statistics output")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
def cli(
    command: str,
    docroot: str | None,
    configdir: str | None,
    interactive: bool,
    verbose: bool,
    quiet: bool,
    dry_run: bool,
) -> None:
    """Install or update MCP Guide templates.

    Commands:
      install  Install templates (default)
      update   Update existing installation
      status   Show installation status
      list     List installed files
    """
    # Validate mutually exclusive flags
    if verbose and quiet:
        raise click.UsageError("--verbose and --quiet are mutually exclusive")

    if dry_run:
        click.echo(f"Dry run mode - {command} - no changes will be made")
        if interactive:
            click.echo("Interactive mode enabled")
        if verbose:
            click.echo("Verbose mode enabled")
        if quiet:
            click.echo("Quiet mode enabled")
        if docroot:
            click.echo(f"Would use docroot: {docroot}")
        if configdir:
            click.echo(f"Would use configdir: {configdir}")
        return

    # Setup logging based on flags
    setup_installer_logging(verbose, quiet)

    asyncio.run(main(command, docroot, configdir, interactive))


async def main(command: str, docroot: str | None, configdir: str | None, interactive: bool) -> None:
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

    logger = logging.getLogger(__name__)

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

        archive_path = docroot_path / ORIGINAL_ARCHIVE

        # Execute command
        if command == "install":
            if config_file.exists() and not custom_docroot:
                # Config exists, just install templates
                result = await install_templates(docroot_path, archive_path)
                await write_version(docroot_path, __version__)

                # Log summary statistics at INFO level
                parts = []
                if result["installed"] > 0:
                    parts.append(f"{result['installed']} installed")
                if result["updated"] > 0:
                    parts.append(f"{result['updated']} updated")
                if result.get("patched", 0) > 0:
                    parts.append(f"{result['patched']} patched")
                if result["unchanged"] > 0:
                    parts.append(f"{result['unchanged']} unchanged")
                if result.get("conflicts", 0) > 0:
                    parts.append(f"{result['conflicts']} conflicts")

                if parts:
                    logger.info(f"{', '.join(parts)} to {docroot_path}")
                else:
                    logger.info(f"Installed to {docroot_path}")
            else:
                # Use integration function for first install or custom docroot
                await install_and_create_config(config_file, docroot_path if custom_docroot else None)
                logger.info(f"Installation complete: {docroot_path}")

            logger.info(f"Config saved: {config_file}")

        elif command == "update":
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

            # Log summary statistics at INFO level
            parts = []
            if result["installed"] > 0:
                parts.append(f"{result['installed']} installed")
            if result["updated"] > 0:
                parts.append(f"{result['updated']} updated")
            if result["patched"] > 0:
                parts.append(f"{result['patched']} patched")
            if result["unchanged"] > 0:
                parts.append(f"{result['unchanged']} unchanged")
            if result["conflicts"] > 0:
                parts.append(f"{result['conflicts']} conflicts")

            if parts:
                logger.info(", ".join(parts))

            # Log conflict warning at WARNING level
            if result["conflicts"] > 0:
                logger.warning("⚠️  Conflicts detected - user changes backed up to orig.* files")

            logger.info(f"Update complete: {docroot_path}")

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
