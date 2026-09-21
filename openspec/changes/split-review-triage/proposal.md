## Why

Independent review collection and finding triage have different stopping points. Coupling them makes a review continue into collation and decision-making even when the user only requested the two fresh review reports.

## What Changes

- Make `workflow-review` stop after it has produced two independent source records, report their paths, and ask the user what to do next.
- Add `workflow-triage` to combine every source record for the active issue into the existing canonical review-inventory format.
- Move pull-request-comment enrichment and the transition to `just-one` from review collection to triage.

## Impact

- Packaged Guide skill templates and the `guide-url-skills` specification.
- Existing source-report and canonical-inventory formats remain compatible.
