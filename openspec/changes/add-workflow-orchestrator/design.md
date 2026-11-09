# Design

## Context

See [proposal.md](proposal.md) for motivation. Existing workflow guidance can
describe phases, and worktree support can isolate a delegated checkout, but no
root-level behaviour joins aligned workflow state to delegated delivery and a
review-ready handback. The client, not Guide, owns Git operations, the shared
handoff file, and platform-specific child-agent creation.

## Goals / Non-Goals

**Goals:**

- Provide a root-bound coordination mode that carries agreed work from
  alignment through implementation evidence and self-review collection.
- Create one complete delegation envelope from current workflow state and any
  explicit child instruction.
- Make worktree inventory visible to command templates while it is current.
- Preserve human authority for scope changes and review triage.

**Non-Goals:**

- Running a server-side scheduler, creating child agents, or executing Git.
- Replacing the existing workflow phases or making every workflow use all of
  them.
- Applying self-review findings or selecting review dispositions.
- Treating a linked-worktree session as an orchestrator.

## Decisions

### Root session is the orchestrator boundary

The orchestrator is a root-bound coordination instruction set, activated after
discussion or planning alignment. It derives work from the root workflow state
and manages the delivery sequence, while linked-worktree sessions remain
limited to their assigned handoff and local workflow file.

This uses the existing project-wide configuration and shared handoff ownership
at the root. A separate persistent orchestration service would require a new
agent identity and external lifecycle management without improving the client
controlled delivery steps.

### Delegation uses a single handoff envelope

Delegation combines the selected issue, current phase, plan when present,
branch, allocated worktree name and sibling path, and child instructions into
one handoff entry at `worktrees.<name>`. The root agent uses the existing
worktree procedure to perform Git creation, locked handoff update, and
platform-specific child spawn.

The child receives only the worktree name and path plus its assigned work. It
starts a fresh Guide session, binds the shared project root and assigned
worktree, then reads its handoff and local workflow file. Parent session IDs
are never passed to children.

### Agent runners are optional execution adapters

Multi-agent execution is expressed as a runner-neutral handoff contract. A
runner is eligible only when it is separately authorised, can access the
assigned worktree, and has Guide MCP available. An eligible runner may be a
non-interactive CLI invocation, a separate interactive agent task, or another
harness-specific worker. Guide does not require a particular runner or create
one itself.

When no eligible runner is available, orchestration retains the handoff and
instructs the root agent to start a compatible agent session manually. This
keeps delegation portable across harnesses while allowing specific clients to
offer convenience adapters later.

### Fan-out invokes Guide work, not runner-specific work

The orchestrator accepts an explicit Guide command or skill invocation and a
selected set of eligible runners. It creates one isolated runner handoff per
selection, all referring to the same assigned worktree when the operation is
read-only, or to distinct worktrees when it modifies code. Each runner starts
its own Guide session and runs the supplied Guide operation.

Multi-agent review is the first consumer: the root agent selects several
runners and `workflow-review`; each receives the same implementation worktree
and records an independently attributable review result. Root orchestration
collects the results for user-led triage. The generic operation deliberately
does not encode Codex, Claude, Cursor, or any other runner's command syntax.

### Orchestration ends at a review-ready handback

The orchestrator may collect validation output, use workflow review, and ask
independent agents to review the implementation worktree. Its internal
self-review loop may correct an objectively demonstrable gap: a failed test or
validation, a direct mismatch with agreed specification, clear scope creep, or
unnecessary complexity whose removal requires no new implementation decision.

When a finding needs architectural or implementation judgement, the loop stops
at the finding. It records the concern in the worktree handoff completion and
returns it with the review target, evidence, and concise triage notes. Fan-out
review findings always follow this latter path. The main agent presents those
findings to the user and executes only user-selected dispositions.

### Inventory is a dynamic template-context projection

`WorktreeTask` remains the session-local inventory owner. Template-context
building projects its cache as `worktree.inventory` with `current`,
`observed_at`, and `paths`. Missing or expired inventory renders as not current
and exposes no usable paths. The projection is dynamic rather than retained in
the general template cache so expiration is observed on every render.

Worktree commands use the same projection: they render refresh guidance when
inventory is not current, consume a current snapshot for allocation and path
authorisation, and invalidate it when issuing worktree-changing guidance.

## Risks / Trade-offs

- [A child-agent platform cannot be invoked] → Render an explicit spawn
  protocol; the root agent carries out platform-specific creation.
- [A stale client inventory can misdirect a handoff] → Use a one-minute TTL,
  invalidate after worktree-changing guidance, and make stale context visible
  to templates.
- [Automated delivery could obscure user control] → Keep scope changes,
  findings disposition, and implementation changes after review exclusively
  with the main root agent and user.
- [Workflow state may omit delegation data] → Require issue selection before
  delegation and include optional plan/instructions only when available.

## Migration Plan

Existing single-worktree workflows remain unchanged. Worktree-enabled root
sessions gain orchestration guidance once the feature is available; no project
configuration migration or stored workflow-file conversion is required.
