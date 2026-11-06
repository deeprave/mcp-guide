# Design

## Context

See `proposal.md` for motivation. `INSTRUCTIONS.md` is a root-level, agent-facing source that conflates universally useful practice, selectable policy, and mcp-guide-only steering. The document store is an all-project opt-in and is not appropriate for this repository-specific migration.

## Goals / Non-Goals

**Goals:**

- Preserve concise, durable guidance in the appropriate shipped template, policy, or repository-local steering location.
- Make generic code and pattern reuse available unconditionally through the default guide profile.
- Offer policy choices only where applicable, including MCP policy only for detected MCP-development projects.
- Remove the superseded repository file and obsolete tool restrictions.

**Non-Goals:**

- Change document ingestion, retrieval, or category behaviour.
- Preserve agent-runtime rules, repeated summaries, or detailed stylistic preferences that do not form durable project guidance.
- Ship mcp-guide-only template steering to other projects.

## Decisions

### Separate generic guidance, policy, and steering

Code and pattern reuse belongs in a generic best-practices guide document and is selected by the default profile. Python async-first, public-API boundaries, module imports, enum-oriented mappings, and pytest fixture preferences remain explicit, selectable policy. Existing JavaScript, Go, Kotlin, and Rust concurrency guidance remains language-specific; no global async-first policy is introduced.

The MCP policy covers the client/server filesystem boundary and modern stateless session identification and binding. Onboarding only asks about it after repository inspection positively identifies MCP development; otherwise it is silently skipped.

Template discovery/rendering guidance remains specific to mcp-guide and moves to `.agents/steering/template-policy.md`. `.agents` is tracked by default. The local review skill is deleted because equivalent mcp-guide skills are shipped; OpenSpec local skills remain.

### Retire obsolete restrictions

The default `checks/instructions` template, the `sed`/`awk`/`perl` policy templates, their onboarding dimension, and their active mcp-guide selections are removed. Personal-error framing and repeated summary material are evicted rather than migrated.

## Risks / Trade-offs

- [New policies could appear in unrelated projects] → onboarding only offers language and MCP policies when inspection establishes they apply.
- [Curating loses useful detail] → retain only guidance that is reusable, selected policy, or local steering; evict obsolete operational history.
