# OpenSpec Integration

mcp-guide integrates with [OpenSpec](https://openspec.dev), an AI-native system
for spec-driven development. Enable it for a project with the `openspec`
project flag to make OpenSpec commands and context available.

## Integration Behaviour

### CLI Availability

Enabling OpenSpec is passive: mcp-guide does not inspect `openspec/config.yaml`,
list a presumed `openspec/` directory, or otherwise validate a project store.
The OpenSpec CLI resolves the applicable store from the active worktree,
including ancestor and named stores.

mcp-guide checks the availability and version of the `openspec` executable with
`openspec --version`. That machine-wide result is reused for 24 hours by
enabled projects. It only establishes whether the CLI is available; it does not
assert that a particular project has an OpenSpec store.

### Change Data

mcp-guide requests `openspec list --json` only when a command or template needs
the change list. The agent returns that CLI result through the normal structured
reply path, after which mcp-guide caches it in the active session for one hour.
An explicit refresh replaces the cached result. Dispatching a mutation-capable
OpenSpec command invalidates relevant cached results, but does not request
replacement data automatically.

There is no filesystem monitoring, directory-mtime refresh, or enable-time
OpenSpec list preflight. If the CLI reports that no OpenSpec root exists, its
own error and remediation are authoritative.

## OpenSpec Commands

When OpenSpec is enabled, these commands are available:

- **`guide://_openspec/init`** — run `openspec init` to initialise a root when
  the CLI advises doing so.
- **`guide://_openspec/propose`** — begin a proposed OpenSpec change through
  the OpenSpec CLI and its resolved schema.
- **`guide://_openspec/list`** — list active changes, requesting and caching
  `openspec list --json` only when needed.
- **`guide://_openspec/show`** — show a specific or current change.
- **`guide://_openspec/status`** — show completion status for a change.
- **`guide://_openspec/validate`** — validate a change against its schema.
- **`guide://_openspec/archive`** — archive a completed change and update the
  resolved main specifications where applicable.
- **`guide://_openspec/schemas`** — discover schemas available to the resolved
  OpenSpec store.

Use `guide://_help` for command help, or `guide://_help/openspec%2F<command>`
for a specific command.

## Workflow Integration

OpenSpec and workflow are independent project capabilities. When both are
enabled, a workflow `issue` is still only a concise dash-delimited work phrase.
It may match an OpenSpec change ID, but it is not required to; tracked-issue
references belong in the separate `tracking` field. OpenSpec commands therefore
accept an explicit change ID or may use the current workflow issue as a
candidate. An unknown candidate is normal for a non-OpenSpec workflow issue and
does not fail the workflow phase.

## OpenSpec Template Context

When OpenSpec is enabled, content templates may use these variables:

- `{{openspec.available}}` — whether the shared CLI availability check passed.
- `{{openspec.version}}` — the detected OpenSpec version.
- `{{openspec.changes}}` — after a successful list response, a grouped mapping
  with `in_progress`, `draft`, and `complete` lists of change objects.
- `{{openspec.show}}` — cached details of the currently shown change, when
  available.
- `{{openspec.status}}` — cached status information for the current change,
  when available.

Before a successful list response, `changes` is intentionally falsey so a
Mustache template can render its request branch. That sentinel is not an
alternative public list shape.

## Configuration

The `openspec` project flag controls this integration:

- `false` or absent — OpenSpec integration is disabled.
- `true` — enable OpenSpec commands and context for the project.
