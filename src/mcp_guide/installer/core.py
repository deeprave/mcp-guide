"""Core installer functionality."""

import difflib
import hashlib
from pathlib import Path
from zipfile import ZipFile

import aiofiles
import patch_ng as patch  # type: ignore[import-untyped]
from anyio import Path as AsyncPath

# System files
ORIGINAL_ARCHIVE = ".original.zip"
VERSION_FILE = ".version"
BACKUP_SUFFIX = ".orig"


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


async def smart_update(current: Path, new: Path, original: Path) -> dict[str, str]:
    """Determine and execute smart update strategy.

    Args:
        current: Current file on filesystem
        new: New file to install
        original: Original file from archive

    Returns:
        Dict with 'action' and 'reason' keys
    """
    if await compare_files(current, new):
        return {"action": "skipped", "reason": "current equals new"}

    # If no original exists, can't track user changes - just replace
    if not original.exists():
        async with aiofiles.open(new, "rb") as src:
            content = await src.read()
        async with aiofiles.open(current, "wb") as dst:
            await dst.write(content)
        return {"action": "replaced", "reason": "no original to compare"}

    if await compare_files(current, original):
        async with aiofiles.open(new, "rb") as src:
            content = await src.read()
        async with aiofiles.open(current, "wb") as dst:
            await dst.write(content)
        return {"action": "replaced", "reason": "no user changes"}

    # User has modified file - backup and try to patch
    backup = current.with_suffix(current.suffix + BACKUP_SUFFIX)
    async with aiofiles.open(current, "rb") as src:
        backup_content = await src.read()

    # Apply patch (patch_ng will try to create its own backup)
    diff = await compute_diff(original, new)
    success = await apply_diff(current, diff)

    if success:
        # Patch succeeded - create our backup
        async with aiofiles.open(backup, "wb") as dst:
            await dst.write(backup_content)
        return {"action": "patched", "reason": "user changes preserved"}

    # Patch failed - restore current file from backup
    async with aiofiles.open(current, "wb") as dst:
        await dst.write(backup_content)
    return {"action": "conflict", "reason": "patch failed"}


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


async def install_file(source: Path, dest: Path) -> bool:
    """Install a single file, creating parent directories if needed.

    Args:
        source: Source file path
        dest: Destination file path

    Returns:
        True if installed, False if skipped (binary)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Try to read as text to detect binary files
    try:
        async with aiofiles.open(source, "r", encoding="utf-8") as f:
            await f.read(1)  # Test read
    except UnicodeDecodeError:
        logger.warning(f"Skipping binary file: {source}")
        return False

    adest = AsyncPath(dest)
    await adest.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(source, "rb") as src:
        content = await src.read()
    async with aiofiles.open(dest, "wb") as dst:
        await dst.write(content)
    asource = AsyncPath(source)
    source_stat = await asource.stat()
    dest.chmod(source_stat.st_mode)
    return True


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
        Dict with 'status' and 'files_installed' keys
    """
    from mcp_guide import __version__

    templates_path = await get_templates_path()
    template_files = await list_template_files()

    # Install all template files
    for template_file in template_files:
        rel_path = template_file.relative_to(templates_path)
        dest_file = docroot / rel_path
        await install_file(template_file, dest_file)

    # Create archive of originals with version
    await create_archive(archive_path, template_files, templates_path)

    # Add version to archive
    with ZipFile(archive_path, "a") as zf:
        zf.writestr(VERSION_FILE, __version__)

    # Write version to docroot
    await write_version(docroot, __version__)

    return {"files_installed": len(template_files)}


async def update_templates(docroot: Path, archive_path: Path) -> dict[str, int]:
    """Update templates using smart strategy.

    Args:
        docroot: Destination directory for templates
        archive_path: Path to originals archive

    Returns:
        Dict with update statistics
    """
    templates_path = await get_templates_path()
    template_files = await list_template_files()

    stats = {"files_processed": 0, "skipped": 0, "replaced": 0, "patched": 0, "conflict": 0}

    for template_file in template_files:
        rel_path = template_file.relative_to(templates_path)
        current_file = docroot / rel_path

        if not current_file.exists():
            # New file - just install
            await install_file(template_file, current_file)
            stats["replaced"] += 1
        else:
            # Existing file - use smart update
            original_in_archive = rel_path
            if await file_exists_in_archive(archive_path, str(original_in_archive)):
                original_content = await extract_from_archive(archive_path, str(original_in_archive))
                original_temp = current_file.parent / f".{current_file.name}.original"
                original_temp.write_bytes(original_content)

                result = await smart_update(current_file, template_file, original_temp)
                stats[result["action"]] += 1

                original_temp.unlink()
            else:
                # No original - just replace
                await install_file(template_file, current_file)
                stats["replaced"] += 1

        stats["files_processed"] += 1

    # Update archive with new originals
    await create_archive(archive_path, template_files, templates_path)

    # Add version to archive
    from mcp_guide import __version__

    with ZipFile(archive_path, "a") as zf:
        zf.writestr(VERSION_FILE, __version__)

    # Write version to docroot
    await write_version(docroot, __version__)

    return stats
