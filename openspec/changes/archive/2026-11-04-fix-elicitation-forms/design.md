# Design

## Context

Elicitation is resolved in `src/mcp_guide/elicitation.py` and invoked from the skill/command
entrypoints. Legacy clients receive sequential elicitation requests; MCP `2026-07-28`
clients receive an `input_required` result with sealed continuation state (see
`docs/developer/authoring-elicitation.md`). The reference form is `workflow-review`, which
declares a `review-target` enum form plus `when`-conditional follow-ups, all with
`fallback: render`.

Observed per agent (see proposal.md): Cursor and Codex work, with varying presentation;
Antigravity usually works; Claude Code and Claude Desktop (modern protocol) show no form and
fail to render the skill, even with `mode=uncommitted`.

## Goals / Non-Goals

**Goals:**
- Identify why modern-protocol Claude clients neither present a form nor render, including
  the `mode=uncommitted` case where no input should be needed.
- Find a form shape and delivery strategy that behaves consistently across all agents.
- Make the no-form fallback deterministic.

**Non-Goals:**
- Migrating additional skills to elicitation (follows once delivery is reliable).
- Changing the declarative frontmatter model unless the exploration shows it is required.

## Decisions

Exploratory: decisions are recorded here as experiments conclude.

1. **Diagnose before changing.** Capture the raw request/response exchange for each agent
   (legacy and modern) against `workflow-review` to separate server faults from client
   limits. Alternative considered: change forms speculatively; rejected as unattributable.
2. **Test form variants incrementally.** Candidate axes: single form versus `when` branching;
   `enum` versus free text; with and without `description`/`title`; with and without
   `fallback: render`; minimal schema. Each variant and its per-agent result is recorded in
   the change's experiment notes and summarised here.
3. **Agent-facing fallback text.** If a client cannot elicit, strengthen the rendered
   instructions (choice list, numbered fallback, "do not begin until selected") so the agent
   responds consistently. Alternative: always require URI keywords; rejected as poor UX.

4. **Decline renders the fallback** (experiment A, verified on Claude Code 2.1.309): a decline on
   a form with `fallback: render` renders without defaults. Alternative C (skip `input_required`
   for modern clients) rejected for now so clients that can show a form still do.
5. **One source resolver for commands and skills** (`mcp_guide/input_sources.py`). The earlier
   command-only restriction was an implementation gap (only the command path ran the resolver),
   not a stated design reason. Sources: `workflow-phases`, `project-categories`,
   `project-collections`, all read from the request's template context.
6. **Body-level handling of the elicited name** in shipped commands, following `workflow/phase`:
   the form's field is `name`, read from `kwargs.name` when no positional argument is given. A new
   schema marker mapping a field to a positional argument was considered and deferred.
7. **Deferred:** document names (dependent on the chosen category), `openspec-changes` (needs the
   client filesystem; see `add-stdio-direct`), and an explicit in-form `cancel` choice.

8. **Inherited-PWD opt-in establishes sharing at startup** (needed to test the prompt route, which
   carries no session id). `initial_filesystem_sharing()` returns shared only for an opted-in stdio
   process whose `PWD` is set, absolute, an existing directory, and the same directory
   (`os.path.samefile`) as the server's working directory; otherwise the probe applies as before.
   The bind itself is protocol-independent: the former `2026-07-28`-only restriction was an oversight, so a
   legacy connection's unbound Session now binds from `PWD` through the same common path (and is
   retained by `bind_project_path`). Alternative (assume shared on opt-in alone) rejected: a wrong `PWD`, as in Claude Desktop code
   mode, would silently bind the wrong project. Conditions are documented in `protocol-and-sessions.md`
   only; `getting-started` and `installation` mention just "stdio only".

## Risks / Trade-offs

- Client behaviour changes between versions → record agent versions with each result.
- A shape that suits modern clients may regress legacy ones → every variant is checked on
  both protocol generations.
- Fallback text relies on agent compliance → keep it explicit and minimal.

## Open Questions

- Does the Claude failure originate in Guide's `input_required` payload, or in the client's
  handling of it? Answered by the first diagnostic task.
