"""Filesystem tool replies dispatch real events to the bound session."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.task_manager import EventType
from mcp_guide.tools.tool_filesystem import (
    SendCommandLocationArgs,
    SendDirectoryListingArgs,
    SendFileContentArgs,
    SendWorkingDirectoryArgs,
    internal_send_command_location,
    internal_send_directory_listing,
    internal_send_file_content,
    internal_send_working_directory,
)
from tests.helpers import create_bound_test_session, request_context_for


@pytest.mark.anyio
async def test_filesystem_replies_dispatch_content_and_metadata_to_the_session(runtime):
    runtime.configuration_service().config_file.write_text("projects: {}\nfeature_flags: {}\n")
    session = await create_bound_test_session(runtime, "filesystem")
    context = await request_context_for(session)
    received = []

    class Receiver:
        def get_name(self):
            return "FilesystemReceiver"

        async def handle_event(self, event_type, data):
            received.append((event_type, data))
            return None

        async def on_tool(self):
            pass

    receiver = Receiver()
    session.task_manager.subscribe(
        receiver, EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY | EventType.FS_COMMAND | EventType.FS_CWD
    )
    args = SendFileContentArgs(
        path="doc.md",
        content="content",
        mtime=123.0,
        category="docs",
        source="agent",
        name="my-doc.md",
        type="agent/instruction",
        force=True,
        metadata={"topic": "test"},
    )
    result = await internal_send_file_content(args, context)
    assert result.success
    assert received[-1] == (
        EventType.FS_FILE_CONTENT,
        {
            "path": "doc.md",
            "content": "content",
            "mtime": 123.0,
            "encoding": "utf-8",
            "category": "docs",
            "source": "agent",
            "name": "my-doc.md",
            "type": "agent/instruction",
            "force": True,
            "metadata": {"topic": "test"},
        },
    )

    entries = [{"name": "readme.md", "type": "file", "size": 1024, "mtime": 123.0}]
    result = await internal_send_directory_listing(SendDirectoryListingArgs(path="docs/", entries=entries), context)
    assert result.success
    assert result.value["count"] == 1
    assert received[-1] == (
        EventType.FS_DIRECTORY,
        {
            "path": "docs",
            "files": entries,
            "pattern": None,
            "recursive": False,
            "count": 1,
        },
    )

    for location in ("/usr/bin/python", None):
        result = await internal_send_command_location(
            SendCommandLocationArgs(command="python", location=location), context
        )
        assert result.success
        assert result.value == {"command": "python", "path": location, "found": location is not None}
        assert received[-1] == (
            EventType.FS_COMMAND,
            {
                "command": "python",
                "path": location or "",
                "found": location is not None,
            },
        )

    result = await internal_send_working_directory(SendWorkingDirectoryArgs(path="/client/project"), context)
    assert result.success
    assert result.value == {"working_directory": "/client/project"}
    assert received[-1] == (EventType.FS_CWD, {"working_directory": "/client/project"})
    count = len(received)
    invalid = await internal_send_file_content(SendFileContentArgs(path=" ", content=""), context)
    assert not invalid.success
    assert invalid.error_type == "validation_error"
    assert set(invalid.error_data) == {"path", "content"}
    denied = await internal_send_directory_listing(SendDirectoryListingArgs(path="../secret", entries=[]), context)
    assert not denied.success
    assert "Path traversal" in denied.error
    assert len(received) == count


@pytest.mark.anyio
@pytest.mark.parametrize(
    "handler,args,boundary,label",
    [
        (
            internal_send_directory_listing,
            SendDirectoryListingArgs(path="docs", entries=[]),
            "fs_send_directory_listing",
            "directory listing",
        ),
        (
            internal_send_command_location,
            SendCommandLocationArgs(command="python", location=None),
            "fs_send_command_location",
            "command location",
        ),
        (
            internal_send_working_directory,
            SendWorkingDirectoryArgs(path="/client/project"),
            "fs_send_working_directory",
            "working directory",
        ),
    ],
)
async def test_wrapper_serialises_unexpected_boundary_errors(runtime, handler, args, boundary, label):
    from tests.helpers import create_unbound_test_session

    context = await request_context_for(create_unbound_test_session(runtime))
    # Normally the filesystem layer returns Result; inject an escaping exception to exercise this boundary.
    with patch(f"mcp_guide.tools.tool_filesystem.{boundary}", new=AsyncMock(side_effect=RuntimeError("Test error"))):
        result = await handler(args, context)
    assert not result.success
    assert result.error_type == "unexpected_error"
    assert result.error == f"Error processing {label}: Test error"
