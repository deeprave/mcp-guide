# Proposal

## Why

Frontmatter elicitation forms are delivered inconsistently across AI agents, so the
interactive entrypoints that depend on them cannot be relied upon. The `workflow-review`
skill (`src/mcp_guide/templates/_skills/workflow/review/SKILL.md.mustache`) is the
reference case:

- **Cursor** and **Codex** work when `mode=uncommitted` is supplied. Without it, Cursor
  presents a form with the declared choices, while Codex usually presents a multi-choice
  field. Antigravity usually works.
- **Claude Code** and **Claude Desktop** present no form and no choices, and fail to render
  the skill at all, even when `mode=uncommitted` is supplied.

The observed difference is protocol generation: Claude Code and Claude Desktop negotiate
MCP `2026-07-28`, where Guide returns an `input_required` result; the other agents use the
legacy MCP elicitation path. Several skills are expected to adopt elicitation forms once
delivery is dependable, so the fault must be understood and fixed first.

## What Changes

This is an exploration issue. Its end objective is that commands, skills, and documents
render reliably in all popular agents. The work proceeds iteratively:

- Reproduce and characterise the failure per agent and protocol generation, including why
  `mode=uncommitted` still fails to render under Claude Code and Claude Desktop.
- Try alternative form shapes and delivery strategies until one behaves consistently across
  agents. Candidates include correcting the modern `input_required` and continuation-state
  handling, simplifying or reshaping schemas (for example enum presentation, single versus
  multiple forms, `when` branching), and changing how elicitation instructions are
  presented to agents that cannot or do not respond to a form.
- Where a client cannot be made to elicit, make the fallback explicit and deterministic so
  the agent can respond consistently (for example the `fallback: render` path with clear
  choice-picker or numbered-list instructions).
- Record each attempted form and its per-agent outcome, and the form that is adopted.
- Update `docs/developer/authoring-elicitation.md` with the supported, verified patterns.

Candidate skills to move to elicitation forms afterwards are out of scope here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-elicitation`: add a requirement for consistent, protocol-independent delivery
  of declared forms to legacy and `2026-07-28` MCP clients, including a deterministic
  fallback when a client does not present a form. Exact requirement wording is refined as
  the exploration converges.

## Impact

- `src/mcp_guide/elicitation.py` and its callers (`tools/tool_resource.py`,
  `prompts/guide_prompt.py`, `render/document_properties.py`).
- `src/mcp_guide/input_sources.py`, which replaces the removed `workflow/command_input.py` and
  fills dynamic choices for commands and skills.
- `src/mcp_guide/session.py` and `server.py` (inherited-`PWD` startup sharing) and the strict-client
  form schema (legacy `title` removal), added as the exploration found them.
- Elicitation-bearing templates, starting with `_skills/workflow/review/SKILL.md.mustache`
  and `_commands/workflow/{phase,review}.mustache`.
- `docs/developer/authoring-elicitation.md`, plus tests under `tests/unit/test_elicitation.py`
  and the MCP v2 protocol fixture.
- No new dependencies. Behaviour for already-working legacy clients must not regress.
