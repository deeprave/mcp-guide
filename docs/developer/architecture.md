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
