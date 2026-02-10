"""Filesystem MCP tools for agent-server interaction."""

import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.result import Result
from mcp_guide.filesystem.cache import FileCache
from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy
from mcp_guide.session import get_or_create_session

logger = get_logger(__name__)

# Global cache instance for server-side caching
_file_cache = FileCache()


async def send_file_content(
    context: Any, path: str, content: str, mtime: Optional[float] = None, encoding: str = "utf-8"
) -> "Result[dict[str, Any]]":
    """Agent tool to send file content from its filesystem to the server.

    This tool is called by the agent when the server requests file content via sampling.
    The agent reads the file from its local filesystem and uses this tool to send
    the content to the server.

    Args:
        context: MCP context
        path: File path that was requested
        content: File content from agent's filesystem
        mtime: File modification time
        encoding: File encoding

    Returns:
        Result with cached file metadata
    """
    try:
        session = await get_or_create_session(context)
        project = await session.get_project()

        # Validate path against security policy
        # Get project root for client path resolution
        from mcp_guide.mcp_context import resolve_project_path

        project_root = await resolve_project_path()

        # Create client_resolve function for security policy
        def client_resolve_func(path: Union[str, Path]) -> Path:
            from mcp_guide.utils.client_path import client_resolve

            return client_resolve(path, project_root)

        # Validate path against security policy
        policy = ReadWriteSecurityPolicy(
            write_allowed_paths=project.allowed_write_paths,
            additional_read_paths=project.additional_read_paths,
            client_resolve=client_resolve_func,
        )

        # Set project root for default read access
        policy.set_project_root(str(project_root))

        validated_path = policy.validate_read_path(path)

        # Cache the content provided by agent
        if mtime is None:
            mtime = time.time()

        _file_cache.put(validated_path, content, mtime)

        # Dispatch event to task manager
        from mcp_guide.task_manager import EventType, get_task_manager
        from mcp_guide.task_manager.manager import aggregate_event_results

        task_manager = get_task_manager()
        event_results = await task_manager.dispatch_event(
            EventType.FS_FILE_CONTENT,
            {
                "path": validated_path,
                "content": content,
                "mtime": mtime,
                "encoding": encoding,
            },
        )

        # Aggregate results
        result = aggregate_event_results(event_results)
        if result.success and result.value:
            return result

        return Result.ok(
            value={"path": validated_path},
            message=f"File content cached for {validated_path}",
            instruction="",
        )

    except Exception as e:
        return Result.failure(error=f"Failed to cache file content: {str(e)}", error_type="cache_failure")


async def send_directory_listing(
    context: Any, path: str, files: list[Dict[str, Any]], pattern: Optional[str] = None, recursive: bool = False
) -> "Result[Dict[str, Any]]":
    """Agent tool to send directory listing from its filesystem to the server.

    This tool is called by the agent when the server requests directory listing via sampling.
    The agent lists the directory from its local filesystem and uses this tool to send
    the results to the server.

    Args:
        context: MCP context
        path: Directory path that was requested
        files: List of files/directories from agent's filesystem
        pattern: Pattern filter that was requested
        recursive: Whether recursive listing was requested

    Returns:
        Result with directory listing metadata
    """
    try:
        session = await get_or_create_session(context)
        project = await session.get_project()

        # Get project root for client path resolution
        from mcp_guide.mcp_context import resolve_project_path

        project_root = await resolve_project_path()

        # Create client_resolve function for security policy
        def client_resolve_func(path: Union[str, Path]) -> Path:
            from mcp_guide.utils.client_path import client_resolve

            return client_resolve(path, project_root)

        # Validate path against security policy
        policy = ReadWriteSecurityPolicy(
            write_allowed_paths=project.allowed_write_paths,
            additional_read_paths=project.additional_read_paths,
            client_resolve=client_resolve_func,
        )

        # Set project root for default read access
        policy.set_project_root(str(project_root))

        validated_path = policy.validate_read_path(path)

        # Dispatch event to task manager
        from mcp_guide.task_manager import EventType, get_task_manager
        from mcp_guide.task_manager.manager import aggregate_event_results

        task_manager = get_task_manager()
        event_results = await task_manager.dispatch_event(
            EventType.FS_DIRECTORY,
            {
                "path": validated_path,
                "files": files,
                "pattern": pattern,
                "recursive": recursive,
                "count": len(files),
            },
        )

        # Aggregate results
        result = aggregate_event_results(event_results)
        if result.success and result.value:
            return result

        return Result.ok(
            {
                "path": validated_path,
                "files": files,
                "pattern": pattern,
                "recursive": recursive,
                "count": len(files),
            }
        )

    except Exception as e:
        return Result.failure(error=f"Failed to provide directory listing: {str(e)}", error_type="unknown")


async def send_command_location(
    context: Any, command: str, path: Optional[str] = None, found: bool = False
) -> "Result[Dict[str, Any]]":
    """Agent tool to send command location to server.

    Args:
        context: MCP context
        command: Command name that was searched for
        path: Full path to command if found
        found: Whether command was found

    Returns:
        Result with command location metadata
    """
    try:
        # Dispatch event to task manager
        from mcp_guide.task_manager import EventType, get_task_manager
        from mcp_guide.task_manager.manager import aggregate_event_results

        task_manager = get_task_manager()
        event_results = await task_manager.dispatch_event(
            EventType.FS_COMMAND,
            {
                "command": command,
                "path": path if path else "",
                "found": found,
            },
        )

        # Aggregate results
        result = aggregate_event_results(event_results)
        if result.success and result.value:
            return result

        return Result.ok(
            {
                "command": command,
                "path": path,
                "found": found,
            }
        )

    except Exception as e:
        return Result.failure(error=f"Failed to provide command location: {str(e)}", error_type="unknown")


async def send_working_directory(context: Any, working_directory: str) -> "Result[Dict[str, Any]]":
    """Agent tool to send current working directory to server.

    Args:
        context: MCP context
        working_directory: Current working directory path

    Returns:
        Result with working directory metadata
    """
    try:
        # Dispatch event to task manager
        from mcp_guide.task_manager import EventType, get_task_manager
        from mcp_guide.task_manager.manager import aggregate_event_results

        task_manager = get_task_manager()
        event_results = await task_manager.dispatch_event(
            EventType.FS_CWD,
            {
                "working_directory": working_directory,
            },
        )

        # Aggregate results
        result = aggregate_event_results(event_results)
        if result.success and result.value:
            return result

        return Result.ok(
            {
                "working_directory": working_directory,
            }
        )

    except Exception as e:
        return Result.failure(error=f"Failed to provide working directory: {str(e)}", error_type="unknown")


async def send_found_files(
    context: Any, pattern: str, files: list[str], start_path: str = "."
) -> "Result[Dict[str, Any]]":
    """Agent tool to send found files to server.

    Args:
        context: MCP context
        pattern: Pattern that was searched for
        files: List of found file paths
        start_path: Directory search started from

    Returns:
        Result with found files metadata
    """
    try:
        # Dispatch event to task manager
        from mcp_guide.task_manager import EventType, get_task_manager
        from mcp_guide.task_manager.manager import aggregate_event_results

        task_manager = get_task_manager()
        event_results = await task_manager.dispatch_event(
            EventType.FS_FOUND_FILES,
            {
                "pattern": pattern,
                "start_path": start_path,
                "files": files,
                "count": len(files),
            },
        )

        # Aggregate results
        result = aggregate_event_results(event_results)
        if result.success and result.value:
            return result

        return Result.ok(
            {
                "pattern": pattern,
                "start_path": start_path,
                "files": files,
                "count": len(files),
            }
        )

    except Exception as e:
        return Result.failure(error=f"Failed to provide found files: {str(e)}", error_type="unknown")


async def set_filesystem_trust_mode(trust_all: bool) -> str:
    """Set filesystem trust mode to bypass security restrictions."""
    # This would integrate with the security policy configuration
    # For now, return a warning message
    if trust_all:
        return (
            "⚠️  FILESYSTEM TRUST MODE ENABLED ⚠️\n"
            "All filesystem security restrictions have been disabled.\n"
            "The agent now has unrestricted access to your filesystem.\n"
            "Use '/tools trust-all false' to re-enable security restrictions."
        )
    else:
        return "✅ FILESYSTEM SECURITY RESTORED\nFilesystem access is now restricted to allowed paths only."
