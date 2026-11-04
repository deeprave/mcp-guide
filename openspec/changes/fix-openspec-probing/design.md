# Design

## Context

See proposal.md for motivation. `openspec-state` is already machine-global and carries validation, version, and check time. The OpenSpec task is recreated for each bound session, so its session-local project-check flag cannot represent the intended machine-wide refresh boundary. Configuration updates already carry previous and current project flags and are delivered through the session queue.

## Goals / Non-Goals

**Goals:**

- Keep ordinary startup, reconnection, and binding silent when the project flag and current global state already agree.
- Make the global `checked` timestamp govern version refreshes exclusively.
- Make the false-to-true project-flag transition the only trigger for repository-asset verification.
- Retain on-demand change discovery.

**Non-Goals:**

- Persisting per-project repository-asset verification state.
- Changing the OpenSpec configuration format, global state structure, or changes-list cache lifetime.
- Treating a project switch or a new session as a flag transition.

## Decisions

### Separate steady-state refresh from enable-transition validation

The task will have two independent request paths. In steady state, an enabled project reads global state: a current timestamp produces no client request, while an absent or stale timestamp produces a version-only request. The request no longer asks for the executable location or lists project assets.

Repository-asset validation will be initiated only from a configuration update whose effective `openspec` project flag changes from disabled to enabled. It will first verify both required assets and, only on success, issue the version request. This deliberately refreshes global state even if it was recently set, because the user explicitly enabled the feature for that project.

Alternative considered: retain a project-local “checked” bit to suppress repeats. Rejected because session recreation loses it and a persisted project marker would add state with no benefit beyond the transition event that already exists.

### Carry transition intent through project-task reconciliation

The task-manager configuration-update path will identify the previous and current effective OpenSpec values and supply an enable-transition intent while it replaces the affected project task. Ordinary project task start receives no such intent, preventing a new session or project binding from being mistaken for a transition.

Alternative considered: infer the transition inside a newly constructed task from current configuration alone. Rejected because the previous value is unavailable there and reconnects are indistinguishable from a true transition.

### Fail closed on incomplete repository assets without mutating global CLI state

If the transition validation cannot verify either `openspec/config.yaml` or `openspec/changes`, Guide will not request the version and will retain `openspec-state`. This avoids recording a CLI refresh that did not satisfy the transition contract.

Alternative considered: reset global state to invalid. Rejected because CLI availability is machine-wide and unrelated to one project's incomplete assets.

## Risks / Trade-offs

- [A project becomes invalid after being enabled] → Guide trusts the explicit flag during steady state; a later explicit disable-to-enable transition performs the defined asset validation.
- [Concurrent sessions observe the same enable transition] → retain the existing queued configuration-update and instruction acknowledgement mechanisms so superseded task activations cannot publish stale replies.
- [A test accidentally models reconnect as a transition] → add lifecycle-level tests that contrast a fresh session with a false-to-true configuration publication.

## Migration Plan

1. Update the task and detection request templates to separate the version-only and asset-validation responses.
2. Route false-to-true transition intent through the existing configuration-update lifecycle.
3. Replace repeat-probe coverage with observable startup, expiry, transition, missing-asset, and on-demand-change tests.
4. Existing `openspec-state` values remain valid; no data migration is required. Reverting restores the prior request behaviour without altering stored state.
