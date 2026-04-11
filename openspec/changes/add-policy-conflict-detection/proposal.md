# Change: Add Policy Conflict Detection

## Why

The policy selection system (introduced in `add-policy-selection`) allows combining multiple policies, but some combinations produce contradictory instructions that reach the agent simultaneously. The mutually-exclusive topic model prevents the clearest conflicts (e.g. `testing/strict` and `testing/minimal` can't both be active), but cross-topic conflicts are not caught. For example, selecting `methodology/tdd` alongside `testing/minimal` sends the agent contradictory guidance — TDD mandates tests-first discipline while minimal testing explicitly deprioritises test structure. A validation layer that detects known cross-topic conflicts at selection time, rather than silently allowing them, would make policy authoring more reliable.

## What Changes

### 1. Define a conflict rule registry

Add a conflict rule registry: a declarative set of rules that identify combinations of active policy selections that are contradictory or redundant. Rules reference topic/policy paths and a human-readable explanation of the conflict.

### 2. Validate on policy selection

When a policy is selected (`:policies/set` or equivalent), run the conflict registry against all currently active policies and the newly requested selection. If a conflict rule matches, surface a clear warning identifying the conflicting policies and the nature of the contradiction.

### 3. Add a `:policies/check` command

Add a `:policies/check` prompt command that runs the conflict validator against the project's full current policy set and reports any detected conflicts. Useful for auditing an existing configuration.

### 4. Conflicts are warnings, not hard blocks

A detected conflict MUST be surfaced as a warning with explanation — it MUST NOT silently prevent the selection from being applied. The user may knowingly combine policies in ways the default rules would flag. The goal is to inform, not to restrict.

### 5. Ship an initial set of conflict rules

Ship a baseline rule set covering the highest-value known cross-topic conflicts, including at minimum:
- `methodology/tdd` + `testing/minimal` — contradictory test discipline
- `git/ops/no-git-ops` + `git/ops/agent-autonomous` — contradictory autonomy level (already mutually exclusive, but defensively caught)
- `methodology/tdd` + `testing/relaxed` — weak conflict worth surfacing
- `pr/no-prs` + `git/ops/agent-autonomous` — pushing without PRs may be intentional but worth flagging

## Dependencies

This change builds on the policy selection model introduced by `add-policy-selection` and SHOULD NOT be implemented before that change is complete.

## Impact

- Affected specs: `project-config`
- Affected code: policy selection handler, new conflict rule registry module, new `:policies/check` command template
