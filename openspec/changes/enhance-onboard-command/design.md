## Overview

This change tightens the `_onboard` command's instruction template so the
interaction behaves like a guided interview instead of an unstructured
questionnaire.

The implementation remains template-only. No new server behavior is introduced;
the change works by giving the agent better ordering, inspection, and
interaction rules inside the existing `onboard.mustache` prompt.

## Current Problems

The current template leaves several gaps:

- It tells the agent to inspect the project, but not to inspect existing guide
  configuration first
- It does not explicitly identify which existing-guide tools/results should be
  used to determine what is already configured
- It does not require an opening summary of current state before questioning
- It does not strictly constrain the questioning loop to one onboarding
  question at a time
- It does not explicitly allow the user to pause onboarding to ask clarifying
  questions
- It does not define a "skip the rest" escape hatch after partial answers have
  already been collected

## Intended Interaction Model

The onboarding flow should operate in four phases:

1. Inspect existing guide/project state
2. Summarize current configuration
3. Ask one onboarding question at a time for remaining dimensions
4. Present a final summary and apply changes only after confirmation

This preserves the existing staged-choices model while making the interview
flow deterministic.

## Inspection Rules

Step 1 should explicitly tell the agent to inspect:

- `guide://_project?verbose` for current project structure and configured
  categories, including the `policies` category
- `list_project_flags` for `onboarded`, `workflow`, and `openspec`
- `list_profiles` so the agent knows which profiles it can propose
- Repository files only as supporting evidence for defaults or applicability

The proposal intentionally removes `list_category_files policies` from the
required inspection set because `guide://_project?verbose` already exposes the
relevant `policies` category configuration. Requiring both would duplicate work
and create unnecessary prompt noise.

## Questioning Rules

Step 2 should be rewritten to define a strict loop:

- Ask exactly one onboarding question at a time
- Wait for the user's response before asking the next onboarding question
- If the user asks a clarifying question, answer it and then resume the
  onboarding flow from the current dimension
- If a dimension is fully configured, skip it silently
- If a dimension is partially configured, mention the current state and ask for
  confirmation or adjustment
- If a likely default can be inferred from project state, propose it
- Accept `skip` or an empty response as skipping the current dimension
- Accept `skip-all` as skipping all remaining dimensions

## `skip-all` Semantics

`skip-all` should behave as an in-session early exit, not as a rollback.

That means:

- Answers already collected in the current onboarding run remain staged
- Remaining unanswered dimensions are treated as skipped
- The flow moves directly to the confirmation summary
- The final apply step still occurs only if the user confirms the staged result

This makes `skip-all` equivalent to "stop asking more onboarding questions"
rather than "discard what we have done so far".

## Confirmation / Apply Behavior

The existing behavior should remain intact:

- Do not apply configuration during questioning
- Present a final summary of staged changes
- Allow the user to adjust before confirmation
- Apply everything only after confirmation
- Mark `onboarded = true` at the end of a successful apply flow

## Implementation Scope

Only [src/mcp_guide/templates/_commands/onboard.mustache](/Users/davidn/Code/mcp-guide/src/mcp_guide/templates/_commands/onboard.mustache)
needs to change.

No Python behavior is required for this change unless implementation uncovers a
missing tool capability, which is not expected from the current design.
