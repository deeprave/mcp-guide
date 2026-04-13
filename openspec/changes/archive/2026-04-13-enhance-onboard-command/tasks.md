## 1. Inspection guidance

- [x] 1.1 Update Step 1 in `src/mcp_guide/templates/_commands/onboard.mustache`
  to require inspection of existing guide configuration before any onboarding
  questions are asked
- [x] 1.2 Add explicit instructions to call `guide://_project?verbose` and use
  it as the primary source of current project/category state, including the
  `policies` category
- [x] 1.3 Add explicit instructions to call `list_project_flags` and inspect at
  least `onboarded`, `workflow`, and `openspec`
- [x] 1.4 Add explicit instructions to call `list_profiles` before asking about
  language/framework profiles
- [x] 1.5 Remove any requirement to call `list_category_files policies` for
  information already available from `guide://_project?verbose`

## 2. Interaction flow

- [x] 2.1 Add an opening summary step that briefly states what is already
  configured before the first onboarding question
- [x] 2.2 Rewrite Step 2 guidance to require exactly one onboarding question at
  a time
- [x] 2.3 Explicitly instruct the agent to wait for the user's response before
  asking the next onboarding question
- [x] 2.4 Explicitly allow the user to ask clarifying questions during
  onboarding, with the agent answering them before resuming the current
  dimension
- [x] 2.5 Explicitly instruct the agent to skip fully configured dimensions
  silently
- [x] 2.6 Explicitly instruct the agent to ask about partially configured
  dimensions and mention the current state when doing so
- [x] 2.7 Explicitly instruct the agent to propose likely defaults when they
  can be inferred from project state
- [x] 2.8 Explicitly accept `skip` or an empty response as skipping the current
  dimension
- [x] 2.9 Add `skip-all` as a valid response that skips all remaining
  onboarding dimensions while preserving answers already collected in the
  current session

## 3. Confirmation / apply wording

- [x] 3.1 Confirm the template still states that no configuration changes are
  applied until the final confirmation step
- [x] 3.2 Confirm the summary step still presents staged choices clearly and
  allows adjustment before apply
- [x] 3.3 Confirm the apply step still uses the existing tools and marks
  `onboarded` as `true` only after successful confirmation/apply

## 4. Validation

- [x] 4.1 Review the final template text end-to-end to ensure the flow reads in
  the intended order: inspect → summarize → ask one question → repeat →
  confirm → apply
- [x] 4.2 Manually verify the template text is internally consistent about
  `skip`, `skip-all`, partial configuration, and clarification handling
- [x] 4.3 Confirm the proposal, design, and task list remain aligned with the
  final template wording before implementation begins
