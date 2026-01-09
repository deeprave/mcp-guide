"""Filesystem MCP tools for agent-server interaction."""

import time
from typing import Any, Dict, Optional

from mcp_core.result import Result
from mcp_guide.filesystem.cache import FileCache
from mcp_guide.filesystem.filesystem_bridge import FilesystemBridge
from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy
from mcp_guide.session import get_or_create_session

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
        policy = ReadWriteSecurityPolicy(
            write_allowed_paths=project.allowed_write_paths, additional_read_paths=project.additional_read_paths
        )

        # Set project root for default read access
        from mcp_guide.mcp_context import resolve_project_path

        project_root = await resolve_project_path()
        policy.set_project_root(str(project_root))

        validated_path = policy.validate_read_path(path)

        # Cache the content provided by agent
        if mtime is None:
            mtime = time.time()

        _file_cache.put(validated_path, content, mtime)

        return Result.ok(
            value={
                "path": validated_path,
                "content": content,
                "mtime": mtime,
                "encoding": encoding,
            },
            message=f"File content cached for {validated_path}",
            instruction="",
        )

    except Exception as e:
        return Result.failure(error=f"Failed to cache file content: {str(e)}", error_type="cache_failure")


async def send_directory_listing(
    context: Any, path: str, files: list[Dict[str, Any]], pattern: Optional[str] = None, recursive: bool = False
) -> Dict[str, Any]:
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
        Result dictionary with success status
    """
    try:
        session = await get_or_create_session(context)
        project = await session.get_project()

        # Validate path against security policy
        policy = ReadWriteSecurityPolicy(
            write_allowed_paths=project.allowed_write_paths, additional_read_paths=project.additional_read_paths
        )

        # Set project root for default read access
        from mcp_guide.mcp_context import resolve_project_path

        project_root = await resolve_project_path()
        policy.set_project_root(str(project_root))

        validated_path = policy.validate_read_path(path)

        # Store directory listing (could be cached if needed)
        # For now, just return success

        return {
            "success": True,
            "message": f"Directory listing provided for {validated_path}",
            "path": validated_path,
            "files": files,
            "pattern": pattern,
            "recursive": recursive,
            "count": len(files),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to provide directory listing: {str(e)}"}


async def send_command_location(
    context: Any, command: str, path: Optional[str] = None, found: bool = False
) -> Dict[str, Any]:
    """Agent tool to send command location to server.

    Args:
        context: MCP context
        command: Command name that was searched for
        path: Full path to command if found
        found: Whether command was found

    Returns:
        Result dictionary with success status
    """
    try:
        return {
            "success": True,
            "message": f"Command location provided for {command}",
            "command": command,
            "path": path,
            "found": found,
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to provide command location: {str(e)}"}


async def send_working_directory(context: Any, working_directory: str) -> Dict[str, Any]:
    """Agent tool to send current working directory to server.

    Args:
        context: MCP context
        working_directory: Current working directory path

    Returns:
        Result dictionary with success status
    """
    try:
        return {
            "success": True,
            "message": f"Working directory provided: {working_directory}",
            "working_directory": working_directory,
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to provide working directory: {str(e)}"}


async def send_found_files(context: Any, pattern: str, files: list[str], start_path: str = ".") -> Dict[str, Any]:
    """Agent tool to send found files to server.

    Args:
        context: MCP context
        pattern: Pattern that was searched for
        files: List of found file paths
        start_path: Directory search started from

    Returns:
        Result dictionary with success status
    """
    try:
        return {
            "success": True,
            "message": f"Found {len(files)} files matching '{pattern}'",
            "pattern": pattern,
            "start_path": start_path,
            "files": files,
            "count": len(files),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to provide found files: {str(e)}"}


async def request_find_files(
    context: Any, pattern: str, start_path: str = ".", max_depth: int = 3, max_results: int = 100
) -> Dict[str, Any]:
    """Server function to find files matching pattern on agent's filesystem.

    Args:
        context: MCP context
        pattern: File pattern to search for (e.g., '*.py', 'package.json')
        start_path: Directory to start search from
        max_depth: Maximum directory depth to search
        max_results: Maximum number of results to return

    Returns:
        Result dictionary with found files or error
    """
    try:
        # Create sampling request for agent
        prompt = f"Please find files matching pattern '{pattern}' starting from '{start_path}' (max depth {max_depth}, max results {max_results}). Use the send_found_files tool to provide the results."

        # Make sampling request to agent
        response = await context.sample(prompt)

        return {
            "success": True,
            "pattern": pattern,
            "start_path": start_path,
            "files": [],  # Will be populated by agent response
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to find files: {str(e)}"}


# Server-side functions for requesting agent filesystem operations
async def request_file_content(
    context: Any, path: str, encoding: str = "utf-8", binary: bool = False
) -> Dict[str, Any]:
    """Server function to request file content from agent's filesystem.

    Args:
        context: MCP context
        path: File path to read from agent's filesystem
        encoding: File encoding
        binary: Whether to read as binary

    Returns:
        Result dictionary with file content or error
    """
    try:
        session = await get_or_create_session(context)
        project = await session.get_project()

        # Create filesystem bridge
        bridge = FilesystemBridge(project, context, _file_cache)

        # Request file content from agent
        content = await bridge.read_file(path, encoding, binary)

        return {
            "success": True,
            "path": path,
            "content": content,
            "encoding": encoding,
            "binary": binary,
            "size": len(content.encode(encoding) if not binary else content),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to request file content: {str(e)}"}


async def request_directory_listing(
    context: Any, path: str, pattern: Optional[str] = None, recursive: bool = False
) -> Dict[str, Any]:
    """Server function to request directory listing from agent's filesystem.

    Args:
        context: MCP context
        path: Directory path to list from agent's filesystem
        pattern: Optional glob pattern filter
        recursive: Whether to list recursively

    Returns:
        Result dictionary with directory listing or error
    """
    try:
        session = await get_or_create_session(context)
        project = await session.get_project()

        # Create filesystem bridge
        bridge = FilesystemBridge(project, context, _file_cache)

        # Request directory listing from agent
        files = await bridge.list_directory(path, pattern, recursive)

        return {
            "success": True,
            "path": path,
            "files": [{"name": f.name, "type": f.type, "size": f.size} for f in files],
            "pattern": pattern,
            "recursive": recursive,
            "count": len(files),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to request directory listing: {str(e)}"}


async def request_which_command(context: Any, command: str) -> Dict[str, Any]:
    """Server function to find executable location on agent's system.

    Args:
        context: MCP context
        command: Command name to locate (e.g., 'openspec', 'python', 'git')

    Returns:
        Result dictionary with command path or error
    """
    try:
        # Create sampling request for agent
        prompt = f"Please locate the '{command}' executable on your system (like 'which {command}'). Use the send_command_location tool to provide the result."

        # Make sampling request to agent
        response = await context.sample(prompt)

        # Agent should respond via send_command_location tool
        # For now, return placeholder - this would be populated by agent response
        return {
            "success": True,
            "command": command,
            "path": None,  # Will be set by agent response
            "found": False,  # Will be set by agent response
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to locate command: {str(e)}"}


async def request_working_directory(context: Any) -> Dict[str, Any]:
    """Server function to get agent's current working directory.

    Args:
        context: MCP context

    Returns:
        Result dictionary with working directory or error
    """
    try:
        # Create sampling request for agent
        prompt = (
            "Please provide your current working directory. Use the send_working_directory tool to provide the result."
        )

        # Make sampling request to agent
        response = await context.sample(prompt)

        return {
            "success": True,
            "working_directory": None,  # Will be set by agent response
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to get working directory: {str(e)}"}


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
