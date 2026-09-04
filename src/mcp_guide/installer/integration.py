"""Integration for automatic template installation on first run."""

from pathlib import Path

import yaml

from mcp_guide.lazy_path import LazyPath


async def install_and_create_config(config_file: Path, docroot: str | Path | None = None) -> None:
    """Install templates and create initial config file.

    Called on first run when config.yaml doesn't exist.
    Used by both automatic first-run and manual CLI installation.

    Args:
        config_file: Path to config.yaml to create
        docroot: Optional custom docroot path. If None, uses the
            config-adjacent default. A supplied value is persisted as written;
            LazyPath is used only for template installation.
    """
    from mcp_guide.installer.core import ORIGINAL_ARCHIVE, install_templates

    config_path = await LazyPath(config_file).aresolve()
    config_file = Path(config_path)
    if docroot is None:
        persisted_docroot: str | Path = config_file.parent / "docs"
        install_root = Path(persisted_docroot)
    else:
        persisted_docroot = docroot if isinstance(docroot, str) else str(docroot)
        install_root = LazyPath(persisted_docroot).resolve()

    archive_path = install_root / ORIGINAL_ARCHIVE
    await install_templates(install_root, archive_path)

    await config_path.parent.mkdir(parents=True, exist_ok=True)
    await config_path.write_text(
        yaml.safe_dump(
            {"docroot": str(persisted_docroot), "projects": {}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
