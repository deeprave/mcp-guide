## Context

`workflow-review` currently obtains independent reports and immediately collates them, which prevents users from receiving independent evidence without starting triage. The canonical combined inventory remains the durable input to `just-one`.

## Decisions

- `workflow-review` owns target selection, workflow-phase transition, OpenSpec validation, and production of exactly two fresh independent source reports. It reports those records and stops for a user decision.
- `workflow-triage` owns collation. It reads every valid report under `Reviews/<issue>/`, rather than only reports from the current session, and writes `Reviews/<issue>.json` in the established format.
- Triage preserves all source references, versions, targets, and scopes, deduplicates only the same underlying defect, and preserves recorded triage state when it updates an existing inventory. A combined finding carries target and scope when its sources agree; otherwise each source reference retains its own context.
- Pull-request comments are examined only after source reports have been collected and only by triage, so reviewers remain independent.
- After writing a stable inventory, `workflow-triage` directs the agent to use `Guide skill "just-one"`; `just-one` remains responsible for user dispositions and implementation authorisation.
