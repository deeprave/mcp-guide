# Change: Improve UX for Document Ingestion and Export

## Why

The exploration in `explore-background-documents` established that the current UX problem is not only raw speed. The more actionable issue is that some document-related workflows block the main interaction unnecessarily even when some clients can hand the work off cleanly.

The findings are strong enough to implement a narrow first-pass improvement now:

- use a template-level handoff capability flag rather than a platform-specific command family
- keep a universal inline fallback for every client
- take advantage of validated handoff-capable clients immediately
- keep further client exploration separate so implementation can start now

This change focuses on UX behavior, not on broader document-semantic changes such as default artifact type or deeper preparation policy.

## What Changes

### 1. Add template-facing agent capability flags

Expose the following template conditionals:

- `agent.has_handoff`
  - defaults to `false`
  - set to `true` only for clients validated for first-pass optimized support
- `agent.is_<normalized-name>`
  - derived from the agent's normalized name
  - intended for light identity-specific wording when needed

This change should use the existing normalized-name approach rather than introducing a new family field.

### 2. Ensure the examined clients have explicit normalized handling

The explored client set should have explicit normalized-name handling and corresponding template conditionals where applicable.

At minimum this includes the clients examined in the exploration:

- Codex
- Codex App
- Amazon Q Developer
- Kiro
- Kiro CLI
- Claude Code
- Claude Desktop
- Cursor
- cursor-agent
- GitHub Copilot
- Gemini CLI
- Windsurf
- Cascade
- Cline
- opencode-ai

### 3. Introduce first-pass handoff support for validated clients

For this change, `agent.has_handoff` should be enabled for the currently validated first-pass set:

- q-dev lineage, including Kiro / Kiro CLI
- Claude Code
- Codex local / in-session

All other clients should default to inline fallback until separately validated.

### 4. Update document and export command templates

The relevant templates should take advantage of handoff where it is useful:

- `_commands/document/add.mustache`
- `_commands/document/add-url.mustache`
- `_commands/export/add.mustache`

`_commands/document/update.mustache` should also be reviewed as part of this change. Because it is already a direct tool mutation rather than a long-running acquisition/preparation workflow, it is expected to remain inline unless implementation finds a concrete reason to branch it.

### 5. Standardize fallback wording

When optimized separate execution is unavailable or cannot actually be used, templates should use a standard fallback explanation before continuing inline.

## Out of Scope

- Expanding first-pass optimized support beyond the currently validated set
- Solving throughput universally across all clients
- Introducing a new command family for document import/export
- Changing document-type defaults or broader prepared-artifact policy in this change
- Treating cloud-hosted background agents as eligible unless they are separately validated for end-to-end MCP continuity

## Impact

- Affected specs:
  - `document-commands`
  - `http-documents`
  - `help-template-system`
  - `content-tools`
- Affected code:
  - `src/mcp_guide/agent_detection.py`
  - `src/mcp_guide/render/cache.py`
  - `src/mcp_guide/templates/_commands/document/add.mustache`
  - `src/mcp_guide/templates/_commands/document/add-url.mustache`
  - `src/mcp_guide/templates/_commands/document/update.mustache`
  - `src/mcp_guide/templates/_commands/export/add.mustache`

## Relationship to Ongoing Exploration

This change deliberately consumes the findings already established and implements the narrow, validated subset now.

Further client examination should continue separately. New clients can be added to `agent.has_handoff` later once validated, without blocking this first-pass UX improvement.
