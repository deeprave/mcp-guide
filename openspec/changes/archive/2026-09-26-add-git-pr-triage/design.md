# Design

## Context

`read-pr-reviews` already defines the intended review-feedback analysis and
durable seen-comment behaviour as a local agent skill. Guide bundles Git skills
as server-owned packages, while `just-one` provides a separate, user-mediated
sequential decision protocol. Pull-request selection must also recognise a PR
already established in active task context. See proposal.md and the delta specs
for the behavioural contract.

## Goals / Non-Goals

**Goals:**
- Package the existing PR-review analysis workflow as a discoverable
  `git-pr-triage` Guide skill.
- Retain durable comment novelty and duplicate detection across invocations.
- Keep collection, analysis, recommendation, and optional sequential decisions
  separate from implementation.

**Non-Goals:**
- Automatically replying to, resolving, or dismissing GitHub review comments.
- Implementing fixes selected during triage.
- Replacing `workflow-triage` or changing the shared review-record format.

## Decisions

### Reuse the established review-comment state shape

The skill will use the established
`{{path.documents}}review-comments/<owner>-<repo>-pr-<number>.json` location
and stable-key/fingerprint model from `read-pr-reviews`.

**Rationale:** Reusing the existing durable contract prevents repeated analysis
and keeps local and bundled skill behaviour aligned.

**Alternative considered:** Keep only an in-memory inventory. Rejected because
later invocations would revisit the same comments.

### Collate all review surfaces before analysis

The skill will form one inventory from inline review threads, review summaries,
and review-related issue comments before deduplicating and recommending action.

**Rationale:** A concern can be represented on more than one GitHub surface;
collation prevents the presentation from overlooking or double-counting it.

**Alternative considered:** Report each API surface separately. Rejected
because it would fragment one review conversation into redundant findings.

### Prefer GitHub MCP, with an explicit `gh` fallback

The rendered guidance will prefer thread-aware GitHub MCP data, falling back to
`gh` only when that data is unavailable or insufficient.

**Rationale:** Thread state and review context improve analysis quality while
maintaining a practical fallback.

**Alternative considered:** Require a single client integration. Rejected
because the skill must remain usable when that integration is unavailable.

### Keep `just-one` opt-in after inventory construction

The skill will build and persist the same stable inventory regardless of how it
is presented. It will provide a grouped report by default and recommend
`just-one` only if the user requests one-at-a-time decisions.

**Rationale:** The user controls verbosity while `just-one` retains its rule
that decisions are collected before any work is executed.

**Alternative considered:** Always invoke `just-one`. Rejected because it
forces a lengthy interactive flow where a concise report is preferred.

## Risks / Trade-offs

- [Provider APIs expose different comment shapes] → Normalise state from stable
  identifiers when present and retain source URLs and fallback keys otherwise.
- [A context-derived pull request is stale or from another repository] → Verify
  its repository before triage and ask the user when it does not match.
- [Current diff context changes while triage runs] → Record source timestamps
  and validate findings against the retrieved current pull-request state.
- [A user changes presentation preference mid-triage] → Preserve the completed
  inventory and switch only the presentation path; do not re-fetch or re-mark
  comments.

## Migration Plan

1. Add the new bundled skill package and its behavioural tests.
2. Verify discovery alongside existing Git skills and review-state persistence.
3. Release without migration: the state file is created lazily on the first
   successful triage report.
