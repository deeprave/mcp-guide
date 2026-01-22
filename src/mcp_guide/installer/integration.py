"""Integration for automatic template installation on first run."""

from pathlib import Path

import aiofiles


async def install_and_create_config(config_file: Path, docroot: Path | None = None) -> None:
    """Install templates and create initial config file.

    Called on first run when config.yaml doesn't exist.
    Used by both automatic first-run and manual CLI installation.

    Args:
        config_file: Path to config.yaml to create
        docroot: Optional custom docroot path. If None, uses default.
    """
    from mcp_guide.config_paths import get_docroot
    from mcp_guide.installer.core import ORIGINAL_ARCHIVE, install_templates

    # Get docroot (custom or default)
    if docroot is None:
        docroot = get_docroot(str(config_file.parent))

    # Install templates
    archive_path = docroot / ORIGINAL_ARCHIVE
    await install_templates(docroot, archive_path)

    # Create config file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(config_file, "w", encoding="utf-8") as f:
        await f.write(f"docroot: {docroot}\nprojects: {{}}\n")
