# MCP Architecture

This diagram describes the server surface created by `create_application()`.  A
`GuideRuntime` is process-global, while each resolved `Session` owns its own
`TaskManager`; task state is not shared between sessions.  The tool groups list
every currently registered Guide tool.  The group heading identifies the core
functionality used by every tool in that group.

![MCP architecture](architecture.mmd)


The common tool decorator resolves the request Session, enforces project binding
where required, invokes `TaskManager.on_tool()`, and normalizes the result to a
native `ToolResult`.  Individual tool implementations then use the Session for
project configuration, client metadata, or task-event dispatch as indicated
above.

## Instruction delivery

`TaskManager` owns queued additional agent instructions. At an outgoing response
boundary, retained clients receive the established structured result field. A
modern client that has negotiated `io.uniquode/mcp-guide-instructions` receives a
typed `notifications/instructions/dispatch` notification on the current FastMCP
request stream instead. The boundary reserves the queue item, confirms it only
after `send_notification()` succeeds, and releases it back to the owning Session
when the stream is unavailable or sending fails.

Modern clients that have not negotiated the extension retain the
`_meta["mcp-guide"]["instructions"]` fallback. Result adapters only serialise the
already-selected delivery representation; they do not access FastMCP transport
state. Notification delivery is not client acknowledgement or authorisation, and
the delivery helper never routes an instruction to a different Guide Session.
