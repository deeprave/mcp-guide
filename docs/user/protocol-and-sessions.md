# Protocol and Sessions

mcp-guide uses FastMCP 4 as its protocol boundary. It supports the modern MCP
protocol revision `2026-07-28` and retained handshake-era clients negotiated by
FastMCP. There is no separate wire protocol named “MCP v2”.

The retained-client bridge has no scheduled end date. It remains available while it
is required by supported clients; a future removal would be announced independently.

## Response instructions

Guide fixes an interaction's protocol type when its Session is established. This
keeps response handling consistent for the life of that interaction, including after
a project switch. A Session cannot change protocol type later.

Retained clients continue to receive task-generated guidance in the existing
`additional_agent_instructions` field of the structured Guide result. MCP
`2026-07-28` clients receive the same single queued instruction in response metadata
at `_meta["mcp-guide"]["instructions"]`; that field is omitted from their structured
Guide result. When no instruction is queued, Guide emits neither the `mcp-guide`
metadata namespace nor its `instructions` key.

This is a compatibility-preserving response representation change. Clients using the
modern protocol should inspect the response `_meta` block as well as structured
content.

## Document cache metadata

When a document resolves to a cache policy, `get_content`, category-content
retrieval, and non-command `guide://` resources include it in response metadata as
`_meta["mcp-guide"]["cache"]`, with `ttl_ms` and `scope` fields. This is Guide's
explicit document-cache contract; it does not restore the former undocumented
`io.modelcontextprotocol/cache-*` metadata keys. Commands, prompts, and other tools
currently do not emit cache metadata, though a future operation may explicitly opt
in with its own resolved policy.

For MIME-formatted multi-document content, each MIME part also carries a standard
`Cache-Control` header based on that file's own policy. This remains useful when the
overall response is no-cache because another contributing document is undeclared.

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
`set_project` call, including one with the same path, is rejected. Use
`switch_project({"path": "..."})` to rebind the root in the retained interaction.

Initial binding never accepts a relative path, even after filesystem verification.
Permitted user/environment expansion must produce an absolute path. Absolute paths
containing `..` are normalised before binding; server CWD is never used to make
relative initial input absolute.

`switch_project` accepts exactly one selection. `switch_project({"name": "..."})`
changes the active Guide configuration within the bound root. Alternatively,
`switch_project({"path": "..."})` rebinds the project root in the retained
interaction and selects the configuration named by the normalised path basename.
Use an absolute client path unless stdio filesystem sharing has been verified.
After verification, the path may also use `~`, `~user`, `$VAR` or `${VAR}`, or
be relative to the current bound root. Do not provide both `name` and `path`.

### Client filesystem verification

The first stdio binding requires an absolute client root. Guide creates a
uniquely named `.mcp-guide-fs-probe-<random-id>` file there and queues a one-time
instruction asking the agent to read it and return its exact contents through
`send_file_content`. The agent must not create or modify the probe. If it cannot
read the file, it should report `unreadable` as instructed.

The response timeout is **60 seconds**, starting when the instruction is attached
to an outgoing response, not when queued. This notification does not confirm
client receipt. A matching response enables shorthand process-wide until the
server restarts. Failure, timeout or disposal of the owning Session leaves it
disabled. Guide removes the probe and its instruction/subscriptions on completion;
there is no automatic retry. Until verification succeeds, supply absolute paths.

Verified sharing permits server-side user, environment and symlink resolution.
Guide assumes the client and server use the same user/home; `~user` and variables
use the server's accounts and environment. Matching access is sufficient; matching
every mount or environment variable is not independently verified. Relative root
switches use the current bound root, never the server working directory.

Stdio alone does not prove sharing: a Docker stdio deployment without the same
project mount at the same absolute path cannot use shorthand. HTTP and HTTPS
always disable shorthand and never send a probe, including localhost HTTP and
container or remote servers. Their roots are normalised lexically without server
symlink resolution. Resolve shorthand on the client and submit an absolute path.

Server-owned configuration paths and docroot retain ordinary server-side expansion.
The optional inherited-`PWD` bootstrap additionally requires already verified stdio
sharing, so it cannot replace the first explicit binding after server startup.

A different selection creates a fresh internal Session under the same public
`session_id`; it does not reconnect the client. Selecting the current name and
root is a no-op unless a previous Session is still expiring.

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

Sessions progress from **unbound → bound → expiring**, then are disposed of.
Unbound Sessions are request-local until initial binding succeeds. A project
switch publishes a fresh bound Session and lets the outgoing Session finish
work already in progress, including configuration saves to its original project.
Its original binding never changes. New requests, including delayed client
replies, use the current Session; no additional client token is needed.

The outgoing Session receives no new scheduling or configuration notifications.
Once its work finishes, Guide disposes of its tasks, listeners, queues and caches.
Disposal runs independently of the successful switch response. Cleanup failures
are logged separately and keep the outgoing Session registered as expiring.
While that Session is expiring, another switch is rejected without changing the
current project, including an otherwise unchanged selection. Try again after
the outstanding work has completed; switches are not queued automatically.

Guide logs the negotiated protocol revision and available client name/version
once at interaction establishment. An internal Session replacement does not
produce another establishment log. These logs exclude session IDs and client paths.
Modern request-local work without a public interaction ID does not emit an
establishment log.

Inactive runtime Sessions expire after one hour, checked at request boundaries. After
expiry, begin a new interaction and bind the project again. A server restart also
clears transient interaction state; durable configuration remains in the shared
configuration file.
Idle disposal uses the same expiring lifecycle: it cannot create a second
expiring Session for an ID, and failed disposal prevents rebinding that ID.

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
