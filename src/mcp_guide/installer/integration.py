"""Integration for automatic template installation on first run."""

from pathlib import Path

import anyio


async def install_and_create_config(config_file: Path, docroot: Path | None = None) -> None:
    """Install templates and create initial config file.

    Called on first run when config.yaml doesn't exist.
    Used by both automatic first-run and manual CLI installation.

    Args:
        config_file: Path to config.yaml to create
        docroot: Optional custom docroot path. If None, uses default.
    """
    from mcp_guide.installer.core import ORIGINAL_ARCHIVE, install_templates

    config_file = Path(config_file).expanduser().resolve()
    if docroot is None:
        docroot = config_file.parent / "docs"
    else:
        docroot = Path(docroot).expanduser().resolve()

    archive_path = docroot / ORIGINAL_ARCHIVE
    await install_templates(docroot, archive_path)

    config_file.parent.mkdir(parents=True, exist_ok=True)
    await anyio.Path(config_file).write_text(f"docroot: {docroot}\nprojects: {{}}\n", encoding="utf-8")
