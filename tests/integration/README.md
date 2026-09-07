# Integration tests

Integration tests exercise observable behaviour across Guide components: real
configuration, files, rendering, session lifecycles and MCP client interactions.
Assert returned content, persisted state and emitted instructions, rather than
registration existence or calls to mocked Guide methods.

## Isolation

Use `mcp_server_factory` for protocol tests. It clears deferred tool registrations,
reloads the requested modules and creates a server with a temporary configuration
and document root. The previous registry is restored after the module finishes.
Python's import cache otherwise prevents decorators from repopulating a cleared
registry. Production registration is deferred and tracked per server; there is
no ToolsProxy singleton.

Use the `runtime` fixture and helpers in `tests/helpers.py` for component tests.
Bind a real project when the behaviour requires one, and construct an explicit
request context. Keep all filesystem writes in pytest temporary directories.

## Coverage and runtime

Preserve both modern and legacy MCP protocol coverage. Legacy protocol support
is not obsolete application-state compatibility.

Combine repeated setup where scenarios form one meaningful behavioural flow.
Parametrise cases with matching setup and assertions. Do not duplicate a protocol
round trip for every unit-level input, or count fewer test functions as evidence
of improved runtime. Compare complete suite runs under the same settings.

Run every pytest command in a persistent foreground terminal and wait for its
complete result. Do not edit tracked worktree files during a run: the safety
fixture treats those writes as a test isolation failure.
