## Why

The guided onboarding command (`_onboard`) produces non-deterministic results: agents
don't inspect existing project state before asking questions, have no guidance on which
tools to call to determine what is already configured, and receive no instruction to ask
one question at a time — causing them to either re-ask already-configured dimensions or
dump all questions at once as a wall of text, defeating the purpose of guided setup.

## What Changes

- **Modify** `src/mcp_guide/templates/_commands/onboard.mustache` — Step 1 gains an
  explicit "Check existing guide configuration" subsection with named tool calls and flag
  names to inspect; Step 2 gains a mandatory one-question-at-a-time rule with skip/partial
  logic; an opening summary of already-configured dimensions is shown before any questions
  are asked
- **No new files** — the change is entirely within the existing onboard template

## Capabilities

### New Capabilities

*(none — this is a template content change only)*

### Modified Capabilities

- `onboard-command`: Step 1 must call `guide://_project?verbose`, `list_project_flags`
  (checking `onboarded`, `workflow`, `openspec`), `list_category_files policies` (to see
  which policy patterns are active, not by reading `guide://policies` verbosely), and
  `list_profiles` (to show available profiles before asking). Step 2 must ask exactly one
  dimension at a time, wait for the user response, skip fully-configured dimensions
  silently, ask about partially-configured dimensions, propose filesystem-detected defaults,
  and accept "skip" or empty response as a valid answer. An opening summary of current
  configuration must be displayed before the first question.

## Impact

- `src/mcp_guide/templates/_commands/onboard.mustache` — sole file changed
- No Python code changes
- No new dependencies
