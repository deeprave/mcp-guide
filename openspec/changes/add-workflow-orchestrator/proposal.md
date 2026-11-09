# Proposal

## Why

Guide supports individual workflow phases and linked worktrees, but it has no
root-bound delivery role that can turn agreed discussion into review-ready work.
Projects need automated coordination of implementation and evidence gathering
without transferring scope or review-disposition authority away from the user.

## What Changes

- Introduce a root-bound workflow orchestrator that begins after discussion or
  planning alignment and coordinates delivery through implementation and
  review preparation.
- Make delegation a first-class orchestration operation: derive the current
  issue, phase, plan, and instructions; use worktree commands to isolate the
  work; create the client-owned handoff; and instruct the parent to spawn a
  fresh worktree agent.
- Define strict authority boundaries: the orchestrator may implement, gather
  proof, self-review, and commission independent reviewers. Self-review may
  correct objectively demonstrable delivery defects, but it must not make
  architectural or implementation decisions or decide review dispositions.
- Return a structured review-ready handback to the main root agent containing
  the implementation location, validation evidence, and triage notes.
- Expose a current, read-only worktree-inventory projection to templates.
  Inventory is session-local, expires after one minute, and is invalidated when
  worktree-changing guidance is issued; commands request client refresh only
  when that projection is absent or stale.
- Add a runner-neutral multi-agent execution feature. Separately authorised
  agent runners can receive a worktree handoff, establish their own Guide
  session, and report completion through the shared workflow and review
  artefacts.
- Allow orchestration to fan out any permitted Guide command or skill to a
  selected set of eligible runners. This includes independent multi-agent
  review, where each reviewer assesses the same worktree and returns its own
  review result for root-led triage.

## Capabilities

### New Capabilities

- `workflow-orchestration`: Root-bound automated delivery coordination,
  worktree delegation, review-ready handback, and review-authority boundaries.
- `multi-agent-execution`: Runner-neutral delegated-agent eligibility,
  handoff bootstrap, isolated Guide-session requirements, and generic
  multi-agent command or skill fan-out.

### Modified Capabilities

- `template-context`: Expose the current worktree-inventory cache safely to
  templates for conditional refresh and delegation guidance.

## Impact

Workflow templates and state, worktree commands and context, session/task
coordination, review guidance, and template-context cache projections. This
does not add a server-side child-agent runtime: the root agent remains
responsible for platform-specific child spawning and client-owned filesystem
updates.
