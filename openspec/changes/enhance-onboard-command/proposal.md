## Why

The guided onboarding command (`_onboard`) produces inconsistent and often poor
interactive behavior. Agents do not reliably inspect the existing guide
configuration before asking questions, so they may re-ask dimensions that are
already configured or miss obvious defaults already visible from project state.
The prompt also does not constrain the interaction loop tightly enough: agents
may ask many onboarding questions at once, may not pause for user clarification,
and have no explicit instruction for a "skip the rest" path after partial
answers have already been collected.

This makes onboarding noisy, repetitive, and less useful than intended.

## What Changes

- **Modify** `src/mcp_guide/templates/_commands/onboard.mustache`
- **Do not add new Python code** — this change is prompt/template behavior only
- **Add** explicit Step 1 instructions to inspect current guide state before
  asking onboarding questions
- **Require** the agent to use `guide://_project?verbose` as the primary source
  of existing category/configuration state, including the `policies` category
- **Require** the agent to inspect project flags via `list_project_flags`,
  specifically checking `onboarded`, `workflow`, and `openspec`
- **Require** the agent to inspect available profiles via `list_profiles`
- **Add** an opening summary of already-configured dimensions before the first
  onboarding question
- **Modify** Step 2 to require exactly one onboarding question at a time
- **Allow** the user to ask clarifying questions between onboarding questions,
  with the agent answering them before resuming onboarding
- **Add** `skip-all` as a valid user response that skips all remaining
  onboarding dimensions while preserving answers already collected in the
  current onboarding session
- **Retain** existing end-of-flow confirmation and apply-all-at-once behavior

## Capabilities

### Modified Capabilities

- `onboard-command`: Step 1 must inspect existing project configuration before
  asking anything, using `guide://_project?verbose`, `list_project_flags`, and
  `list_profiles`. The command must summarize current configuration first, skip
  fully configured dimensions silently, ask about partially configured or
  missing dimensions, propose filesystem- or config-detected defaults, ask
  exactly one onboarding question at a time, allow clarifying user questions,
  accept per-question `skip` / empty responses, and accept `skip-all` to stop
  the remaining onboarding flow early

## Impact

- `src/mcp_guide/templates/_commands/onboard.mustache` — sole implementation
  file changed
- No new runtime dependencies
- No Python code changes expected
- No data model changes expected
