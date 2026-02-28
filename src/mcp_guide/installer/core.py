"""Core installer functionality."""

import difflib
import hashlib
from pathlib import Path
from zipfile import ZipFile

import aiofiles
import patch_ng as patch  # type: ignore[import-untyped]
from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger

# System files
ORIGINAL_ARCHIVE = ".original.zip"
VERSION_FILE = ".version"
BACKUP_PREFIX = "orig"

logger = get_logger(__name__)


def get_backup_path(file_path: Path) -> Path:
    """Get backup path for a file using standard naming convention.

    Args:
        file_path: Original file path

    Returns:
        Path for backup file (orig.<filename>)
    """
    return file_path.parent / f"{BACKUP_PREFIX}.{file_path.name}"


async def _backup_file(path: Path) -> Path:
    """Create a backup of the given file and return the backup path.

    Args:
        path: Path to file to backup

    Returns:
        Path to the created backup file
    """
    backup_path = get_backup_path(path)
    async with aiofiles.open(path, "rb") as src:
        async with aiofiles.open(backup_path, "wb") as dst:
            await dst.write(await src.read())
    return backup_path


async def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file asynchronously.

    Args:
        filepath: Path to the file to hash

    Returns:
        Hexadecimal digest of the file's SHA256 hash
    """
    hasher = hashlib.sha256()
    async with aiofiles.open(filepath, "rb") as f:
        while chunk := await f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


async def compare_files(file1: Path, file2: Path) -> bool:
    """Compare two files by computing their SHA256 hashes.

    Args:
        file1: First file path
        file2: Second file path

    Returns:
        True if files are identical, False otherwise
    """
    # Quick size check first
    afile1 = AsyncPath(file1)
    afile2 = AsyncPath(file2)
    stat1 = await afile1.stat()
    stat2 = await afile2.stat()
    if stat1.st_size != stat2.st_size:
        return False

    # Compute and compare hashes
    hash1 = await compute_file_hash(file1)
    hash2 = await compute_file_hash(file2)

    return hash1 == hash2


async def create_archive(archive_path: Path, files: list[Path], base_dir: Path) -> None:
    """Create a zip archive containing the specified files.

    Args:
        archive_path: Path where the zip archive will be created
        files: List of file paths to include in the archive
        base_dir: Base directory for computing relative paths in archive
    """
    readme_content = """# Original Files Archive

This archive contains the original versions of installed files.

**DO NOT MODIFY** the contents of this archive.

The installer uses these files to:
- Detect if you have made changes to installed files
- Apply smart updates that preserve your modifications
- Generate diffs between original and new versions

If this archive is modified or deleted, the installer cannot determine
which changes are yours and will replace files without attempting to
merge your modifications.
"""

    with ZipFile(archive_path, "w") as zf:
        zf.writestr("README.md", readme_content)
        for file_path in files:
            arcname = file_path.relative_to(base_dir)
            zf.write(file_path, arcname)


async def extract_from_archive(archive_path: Path, filename: str) -> bytes:
    """Extract a file's content from a zip archive.

    Args:
        archive_path: Path to the zip archive
        filename: Name of the file to extract (relative path within archive)

    Returns:
        File content as bytes
    """
    with ZipFile(archive_path, "r") as zf:
        return zf.read(filename)


async def file_exists_in_archive(archive_path: Path, filename: str) -> bool:
    """Check if a file exists in a zip archive.

    Args:
        archive_path: Path to the zip archive
        filename: Name of the file to check (relative path within archive)

    Returns:
        True if file exists in archive, False otherwise
    """
    with ZipFile(archive_path, "r") as zf:
        return filename in zf.namelist()


async def compute_diff(original: Path, current: Path) -> str:
    """Compute unified diff between two text files.

    Args:
        original: Path to original file
        current: Path to current (modified) file

    Returns:
        Unified diff as string
    """
    async with aiofiles.open(original, "r") as f:
        original_lines = (await f.read()).splitlines(keepends=True)

    async with aiofiles.open(current, "r") as f:
        current_lines = (await f.read()).splitlines(keepends=True)

    diff_lines = difflib.unified_diff(
        original_lines,
        current_lines,
        fromfile=str(original),
        tofile=str(current),
    )

    return "".join(diff_lines)


async def apply_diff(target: Path, diff_content: str) -> bool:
    """Apply a unified diff to a target file.

    Args:
        target: Path to file to patch
        diff_content: Unified diff content as string

    Returns:
        True if patch applied successfully, False otherwise
    """
    try:
        # Rewrite diff headers to use target filename
        lines = diff_content.splitlines(keepends=True)
        rewritten = []
        for line in lines:
            if line.startswith("--- "):
                rewritten.append(f"--- {target.name}\n")
            elif line.startswith("+++ "):
                rewritten.append(f"+++ {target.name}\n")
            else:
                rewritten.append(line)

        patchset = patch.fromstring("".join(rewritten).encode())
        if not patchset:
            return False
        result = patchset.apply(root=str(target.parent))
        return bool(result)
    except Exception:
        return False


async def get_templates_path() -> Path:
    """Get the path to the templates directory in the package.

    Returns:
        Path to templates directory
    """
    import mcp_guide

    package_path = Path(mcp_guide.__file__).parent

    # Check if templates is in package (installed)
    templates_in_package = package_path / "templates"
    if templates_in_package.exists():
        return templates_in_package

    # Fall back to project root (development)
    project_root = package_path.parent.parent
    templates_in_root = project_root / "templates"
    if templates_in_root.exists():
        return templates_in_root

    raise FileNotFoundError("Templates directory not found")


async def list_template_files() -> list[Path]:
    """List all template files recursively, excluding dot-prefixed files.

    Returns:
        List of Path objects for all template files (excluding hidden files)
    """
    templates_path = await get_templates_path()
    return [f for f in templates_path.rglob("*") if f.is_file() and not f.name.startswith(".")]


async def _extract_original_to_temp(archive_path: Path, rel_path: str, dest: Path) -> Path:
    """Extract original file from archive to temporary location.

    Args:
        archive_path: Path to archive
        rel_path: Relative path of file in archive
        dest: Destination file path (used for temp file location)

    Returns:
        Path to temporary file containing original content
    """
    original_content = await extract_from_archive(archive_path, rel_path)
    original_temp = dest.parent / f".{dest.name}.original"
    async with aiofiles.open(original_temp, "wb") as f:
        await f.write(original_content)
    return original_temp


def _create_stats_dict() -> dict[str, int]:
    """Create a new statistics dictionary with standard keys.

    Returns:
        Dict with operation counts initialized to 0
    """
    return {
        "installed": 0,
        "updated": 0,
        "patched": 0,
        "unchanged": 0,
        "conflicts": 0,
        "skipped_binary": 0,
    }


def _map_result_to_stat_key(result: str) -> str:
    """Map install_file result to stats dictionary key.

    Args:
        result: Result string from install_file

    Returns:
        Stats key (handles singular/plural mapping)
    """
    return "conflicts" if result == "conflict" else result


async def _copy_file_with_permissions(source: Path, dest: Path) -> None:
    """Copy file content and permissions from source to dest.

    Args:
        source: Source file path
        dest: Destination file path
    """
    adest = AsyncPath(dest)
    await adest.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(source, "rb") as src:
        content = await src.read()
    async with aiofiles.open(dest, "wb") as dst:
        await dst.write(content)
    asource = AsyncPath(source)
    source_stat = await asource.stat()
    dest.chmod(source_stat.st_mode)


async def install_file(
    source: Path, dest: Path, archive_path: Path | None = None, archive_name: str | None = None
) -> str:
    """Install a single file using smart update strategy.

    Args:
        source: Source file path
        dest: Destination file path
        archive_path: Optional path to originals archive for comparison
        archive_name: Optional relative path for archive lookup (defaults to dest.name)

    Returns:
        Operation status: "installed", "updated", "patched", "unchanged", "conflict", "skipped_binary"
    """
    # Try to read as text to detect binary files
    try:
        async with aiofiles.open(source, "r", encoding="utf-8") as f:
            await f.read(1)  # Test read
    except UnicodeDecodeError:
        logger.warning(f"Skipping binary file: {source}")
        return "skipped_binary"

    # If dest doesn't exist, install new file
    adest = AsyncPath(dest)
    if not await adest.exists():
        await _copy_file_with_permissions(source, dest)
        logger.debug(f"Installed new file: {dest}")
        return "installed"

    # Compare source and dest
    if await compare_files(source, dest):
        logger.debug(f"Skipping unchanged file: {dest}")
        return "unchanged"

    # Check if we have an archive with the original version
    has_archive = archive_path is not None and archive_path.exists()
    original_name = archive_name or dest.name

    if has_archive and archive_path is not None:
        has_original = await file_exists_in_archive(archive_path, original_name)
    else:
        has_original = False

    if has_original and archive_path is not None:
        original_temp = await _extract_original_to_temp(archive_path, original_name, dest)
        original_temp_async = AsyncPath(original_temp)

        try:
            # Check if source has changed from original
            if await compare_files(source, original_temp):
                # Source unchanged - preserve user modifications
                logger.debug(f"Unchanged template, preserving user modifications: {dest}")
                return "unchanged"

            # Compare dest with original
            if await compare_files(dest, original_temp):
                # Unmodified - just update
                await _copy_file_with_permissions(source, dest)
                logger.debug(f"Updated file: {dest}")
                return "updated"

            # User modified - try to patch
            diff = await compute_diff(original_temp, source)
            success = await apply_diff(dest, diff)

            if success:
                # Patch succeeded
                logger.debug(f"Patched user modifications: {dest}")
                return "patched"

            # Patch failed - backup and replace
            backup_path = await _backup_file(dest)
            await _copy_file_with_permissions(source, dest)
            logger.warning(f"⚠️  Conflict: {dest} (backed up to {backup_path})")
            return "conflict"
        finally:
            # Always cleanup temp file
            await original_temp_async.unlink(missing_ok=True)

    # No original in archive - cannot distinguish user modifications from template changes
    # Backup and replace with warning
    backup_path = await _backup_file(dest)
    await _copy_file_with_permissions(source, dest)
    logger.warning(f"⚠️  No archive: {dest} backed up to {backup_path} (cannot verify user changes)")
    return "conflict"


async def install_directory(source: Path, dest: Path) -> None:
    """Install entire directory tree.

    Args:
        source: Source directory
        dest: Destination directory
    """
    adest = AsyncPath(dest)
    await adest.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(source)
            dest_file = dest / rel_path
            await install_file(item, dest_file)


async def write_version(docroot: Path, version: str) -> None:
    """Write version file to docroot.

    Args:
        docroot: Document root directory
        version: Version string to write
    """
    version_path = docroot / VERSION_FILE
    async with aiofiles.open(version_path, "w", encoding="utf-8") as f:
        await f.write(version)


async def read_version(docroot: Path) -> str | None:
    """Read version file from docroot.

    Args:
        docroot: Document root directory

    Returns:
        Version string or None if file doesn't exist
    """
    version_path = docroot / VERSION_FILE
    if not version_path.exists():
        return None
    async with aiofiles.open(version_path, "r", encoding="utf-8") as f:
        return (await f.read()).strip()


async def install_templates(docroot: Path, archive_path: Path) -> dict[str, int]:
    """Install templates to docroot and create originals archive.

    Args:
        docroot: Destination directory for templates
        archive_path: Path where originals archive will be created

    Returns:
        Dict with operation counts: installed, updated, patched, unchanged, conflicts, skipped_binary
    """
    from mcp_guide import __version__

    templates_path = await get_templates_path()
    template_files = await list_template_files()

    stats = _create_stats_dict()

    # Install all template files
    for template_file in template_files:
        rel_path = template_file.relative_to(templates_path)
        dest_file = docroot / rel_path
        result = await install_file(
            template_file, dest_file, archive_path if archive_path.exists() else None, str(rel_path)
        )
        stat_key = _map_result_to_stat_key(result)
        stats[stat_key] += 1

    # Create archive of originals with version
    await create_archive(archive_path, template_files, templates_path)

    # Add version to archive
    with ZipFile(archive_path, "a") as zf:
        zf.writestr(VERSION_FILE, __version__)

    # Write version to docroot
    await write_version(docroot, __version__)

    return stats


async def update_templates(docroot: Path, archive_path: Path) -> dict[str, int]:
    """Update templates using smart strategy.

    Args:
        docroot: Destination directory for templates
        archive_path: Path to originals archive

    Returns:
        Dict with operation counts: installed, updated, patched, unchanged, conflicts, skipped_binary
    """
    templates_path = await get_templates_path()
    template_files = await list_template_files()

    stats = _create_stats_dict()

    for template_file in template_files:
        rel_path = template_file.relative_to(templates_path)
        current_file = docroot / rel_path

        # Use install_file for all cases - it handles everything
        result = await install_file(template_file, current_file, archive_path, str(rel_path))
        stat_key = _map_result_to_stat_key(result)
        stats[stat_key] += 1

    # Update archive with new originals
    await create_archive(archive_path, template_files, templates_path)

    # Add version to archive
    from mcp_guide import __version__

    with ZipFile(archive_path, "a") as zf:
        zf.writestr(VERSION_FILE, __version__)

    # Write version to docroot
    await write_version(docroot, __version__)

    return stats
