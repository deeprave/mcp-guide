# See src/mcp_guide/tools/README.md for tool documentation standards

"""Documentation update tool."""

from pathlib import Path
from typing import Optional

import aiofiles
from anyio import Path as AsyncPath
from pydantic import Field

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.file_lock import lock_update
from mcp_guide.installer.core import update_documents as installer_update_documents
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_NO_PROJECT, INSTRUCTION_NO_PROJECT
from mcp_guide.session import get_or_create_session

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


__all__ = ["internal_update_documents"]


class UpdateDocumentsArgs(ToolArguments):
    """Arguments for update_documents tool."""

    force: bool = Field(default=False, description="If True, update even if version hasn't changed")


async def _read_version(docroot: Path) -> str | None:
    """Read version from docroot."""
    version_path = docroot / ".version"
    if not await AsyncPath(version_path).exists():
        return None
    async with aiofiles.open(version_path, "r", encoding="utf-8") as f:
        return (await f.read()).strip()


async def _perform_update(lock_path: Path, docroot: Path, archive_path: Path) -> dict[str, int]:
    """Perform the actual update with locking."""
    return await installer_update_documents(docroot, archive_path)


@toolfunc(UpdateDocumentsArgs)
async def internal_update_documents(
    args: UpdateDocumentsArgs,
    ctx: Optional[Context] = None,  # type: ignore
) -> Result[dict]:  # type: ignore[type-arg]
    """Update documentation files in the current project.

    Checks for version changes and updates files using smart merge strategy.
    Uses file locking to prevent concurrent updates.

    Args:
        args: Tool arguments with force flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing update statistics
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(
            error=str(e),
            error_type=ERROR_NO_PROJECT,
            instruction=INSTRUCTION_NO_PROJECT,
        )

    docroot = Path(await session.get_docroot())
    archive_path = docroot / ".originals.zip"

    # Ensure docroot exists
    await AsyncPath(docroot).mkdir(parents=True, exist_ok=True)

    # Check version unless force
    if not args.force:
        from mcp_guide import __version__

        current_version = await _read_version(docroot)
        if current_version == __version__:
            return Result.ok(value={"message": f"Already at version {__version__}", "updated": False})

    # Use lock_update with lock path
    lock_path = docroot / ".update"
    stats = await lock_update(lock_path, _perform_update, docroot, archive_path)

    return Result.ok(
        value={
            "message": "Documentation updated successfully",
            "updated": True,
            "stats": stats,
        }
    )
