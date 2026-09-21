## 1. Skill separation

- [x] 1.1 Make `workflow-review` stop after reporting its two independent source records and requesting the user's next action.
- [x] 1.2 Add `workflow-triage` to collate all source reports for the active issue and then invoke `just-one`.

## 2. Specification and verification

- [x] 2.1 Add delta requirements for the review/triage boundary and canonical inventory ownership.
- [x] 2.2 Validate the change and run focused package-rendering coverage (43 focused tests passed).
- [x] 2.3 Preserve target and scope on each combined finding or source reference, without making either a triage gate.
