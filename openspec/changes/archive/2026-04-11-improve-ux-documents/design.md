# Design: Improve UX for Document Ingestion and Export

## Purpose

This change applies the actionable subset of the exploration findings immediately.

The implementation should stay simple:

- template-level branching
- narrow capability exposure
- validated first-pass clients only
- standardized inline fallback everywhere else

## Design Goals

1. Improve user experience without introducing a new command surface
2. Keep fallback behavior universal and predictable
3. Avoid overfitting templates to one client's vocabulary
4. Preserve a small, maintainable capability interface for templates
5. Leave room for later client expansion without redesigning the feature

## Non-Goals

- Reworking the entire ingestion architecture
- Standardizing every client-specific nuance in this change
- Adding Python orchestration for detached work beyond capability flags needed by templates
- Changing default document semantics such as prepared-artifact defaults

## Core Model

The UX split is execution-mode based:

```text
handoff-capable client
  -> separate execution path when truly available
  -> final completion/failure report
  -> standardized inline fallback if handoff cannot actually be used

non-handoff client
  -> inline execution path
  -> same command semantics
```

The semantic workflow of the commands does not change. Only the staging changes.

## Template Context Contract

### `agent.has_handoff`

Expose a new boolean template variable:

```text
agent.has_handoff
```

Rules:

- defaults to `false`
- must be explicit rather than inferred inside templates
- should only be `true` for clients validated for first-pass optimized support

Initial set:

- q-dev lineage, including Kiro / Kiro CLI
- Claude Code
- Codex local / in-session

### `agent.is_<normalized-name>`

Expose boolean membership flags derived from the normalized agent name:

```text
agent.is_codex
agent.is_q_dev
agent.is_claude
agent.is_cursor
agent.is_copilot
agent.is_gemini
agent.is_windsurf
agent.is_cline
agent.is_opencode
agent.is_unknown
```

Rules:

- names should reflect the existing normalized-name system
- flags exist for template readability
- templates should prefer `agent.has_handoff` for behavior branching
- `agent.is_<name>` should be reserved for light identity-specific phrasing only

## Agent Normalization and Coverage

This change should ensure the explored client set has explicit normalized handling.

The examined set from the exploration is:

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

Important detail from the exploration:

- Amazon Q Developer, Kiro, and Kiro CLI all identify under the same lineage and should continue to normalize to `q-dev`

This means the first-pass optimized branch should rely on:

```text
agent.is_q_dev
```

not a separate `agent.is_kiro`.

## Template Branching Strategy

Templates should branch on behavior first:

```mustache
{{#agent.has_handoff}}
optimized handoff-oriented instructions
{{/agent.has_handoff}}

{{^agent.has_handoff}}
standard inline fallback instructions
{{/agent.has_handoff}}
```

Identity flags may then refine wording inside the handoff branch if needed, but they should not be the primary branch selector.

## Command-Specific Design

### `document/add`

Use `agent.has_handoff` to allow a separate execution path for file-read plus `send_file_content` workflows when the client supports it.

The branch should:

- preserve the existing tool call shape
- preserve current arguments and metadata behavior
- use standardized fallback wording before continuing inline when handoff is unavailable in practice

### `document/add-url`

Use `agent.has_handoff` for the same reason, but this command benefits even more because it may involve:

- fetch
- transform
- final `send_file_content`

The same standardized fallback wording should apply.

### `export/add`

Use `agent.has_handoff` because export is a simpler but still potentially blocking workflow:

- call `export_content`
- write returned raw content to disk
- verify write success

This is simpler than ingestion but still benefits from separate execution where supported.

### `document/update`

Review this template in the same change, but the default expectation is:

- remain inline
- do not add a handoff branch unless implementation finds a concrete long-running case worth supporting

This keeps the change aligned with “where possible” rather than forcing handoff into a direct mutation command.

## Standardized Fallback Wording

When optimized separate execution is unavailable or cannot actually be used, the command should use standardized fallback wording before continuing inline.

This wording should be:

- short
- behavior-oriented
- consistent across commands

The exact final string can be implementation-defined, but it should express:

```text
separate execution is not available here
continuing inline instead
```

## Validation Scope

This change should validate only the immediate first-pass set:

- q-dev lineage, including Kiro / Kiro CLI
- Claude Code
- Codex local / in-session

Explicitly out for this change:

- Cursor / cursor-agent
- GitHub Copilot
- Codex cloud
- Claude Desktop
- Windsurf / Cascade
- opencode-ai
- Gemini CLI
- Cline

These remain future candidates or fallback-only clients unless a later change validates them further.

## Rationale

This design is intentionally narrow because it uses findings that are already strong:

- handoff is useful as UX staging
- fallback must remain universal
- Codex local is now validated strongly enough to stay in scope
- Cursor is not

That makes a small, practical first-pass implementation defensible now.
