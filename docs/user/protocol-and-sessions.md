# Protocol and Sessions

mcp-guide uses FastMCP 4 as its protocol boundary. It supports the modern MCP
protocol revision `2026-07-28` and retained handshake-era clients negotiated by
FastMCP. There is no separate wire protocol named “MCP v2”.

The retained-client bridge has no scheduled end date. It remains available while it
is required by supported clients; a future removal would be announced independently.

## Client migration

Existing retained clients continue to use their FastMCP connection identity. They do
not need to replay an identifier returned by Guide.

Modern `2026-07-28` clients bind an interaction with:

```
set_project({"path": "/absolute/client/path/to/project"})
```

The successful result includes `session_id`. The client must provide that value as the
`session_id` argument on later project-bound tool calls. It is an opaque value: pass it
through unchanged and do not construct, alter, or log it.

Clients that read `guide://` resource templates directly must provide the same value
as the URI query parameter, for example:

```
guide://_status?session_id=<session_id>
```

The `read_resource` tool accepts `session_id` as its normal tool argument. This is
needed because rendered Guide resources can depend on the interaction's selected
project, agent details, and feature configuration.

## Project and configuration identity

`set_project` is an agent-facing operation, not a project-name selector. Its required
`path` is the absolute path on the agent's filesystem. Guide derives the displayed
project name and a path hash from that root, then binds the interaction once. A later
`set_project` call, including one with the same path, is rejected. Start a new
interaction to select another root.

`switch_project(name)` changes only the active Guide configuration within the bound
root. It never changes the project root and rejects filesystem paths.

Configuration identity is strict: a stored configuration is usable only when both its
`<project-name>-<hash>` key and stored hash match the bound root. Hashless, malformed,
and mismatched entries are ignored by normal project selection and listing. Guide does
not automatically migrate them.

To copy an existing project configuration, bind the intended current project and run
`clone_project({"from_project": "old-name"})`. With an unhashed source name, clone
lookup uses the first strict configuration whose project name is `old-name` in
configuration order. To select a particular configuration, provide its exact
`old-name-<hash>` key. Only the current bound project's valid hashed configuration is
updated.

`clone_project` no longer accepts a target project. Its destination is always the
active configuration of the bound interaction.

## Interaction state and expiry

GuideRuntime keeps mutable interaction state—including instruction queues, rendering
caches, task state, and active configuration—isolated by session owner. Different
clients and subagents receive separate Sessions even when they select the same root;
they can share durable project configuration but not transient task state.

Inactive runtime Sessions expire after one hour, checked at request boundaries. After
expiry, begin a new interaction and bind the project again. A server restart also
clears transient interaction state; durable configuration remains in the shared
configuration file.

## Operational downgrade and reconnect

This change does not rewrite the configuration-file format. If an operator needs to
replace a running build with an earlier one, restart the server using that build and
have clients reconnect; they must bind a project again because interaction state is
transient. No configuration rollback or migration is required. An older build may
still interpret entries that the strict current build ignores, so configuration should
be reviewed rather than modified merely to support a temporary downgrade.

## HTTP and HTTPS

HTTP and HTTPS use FastMCP's Streamable HTTP application at `/mcp` by default. A path
prefix is followed by `/mcp`, such as `/api/mcp`. Install the HTTP optional dependency
before serving these transports:

```
uv sync --extra http
```

Use HTTPS for network traffic that requires transport confidentiality or integrity.
The HTTP endpoint negotiates the MCP protocol revision through FastMCP; do not add
custom cookies, headers, or a separate Guide session token.

For installation commands and TLS configuration, see [Installation](installation.md).
