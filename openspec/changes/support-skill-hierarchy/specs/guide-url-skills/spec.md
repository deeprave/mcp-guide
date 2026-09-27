## MODIFIED Requirements

### Requirement: Just-one finding triage skill

The system SHALL serve `triage-items` as a packaged Guide skill for any stable
inventory of items. It SHALL collect the user's decision for every item before
any authorised follow-up.

#### Scenario: Present a finding

- **WHEN** the agent begins `triage-items` triage with a fixed inventory of
  items
- **THEN** it SHALL present exactly one item at a time
- **AND** each presentation SHALL include its fixed `current/total` position,
  P1-to-P6 priority, short description, analysis, and recommendation
- **AND** it SHALL combine brief target and scope on one line when both are
  supplied

#### Scenario: Record a decision without editing

- **WHEN** the user accepts, declines, discusses, or varies the current item
- **THEN** the agent SHALL record the resulting disposition in an existing
  canonical inventory, a user-requested `Triage/<derived-key>.json` ledger, or
  a clear in-conversation record
- **AND** SHALL NOT perform follow-up while any item remains undecided

#### Scenario: Confirm collected actions

- **WHEN** every item has a recorded disposition
- **THEN** the agent SHALL show the accepted follow-up list
- **AND** SHALL request explicit user authorisation before a local change or
  external action
- **AND** SHALL perform only the specifically authorised follow-up

### Requirement: Durable review finding records

The workflow review skill SHALL record each independent review in
`{{path.documents}}Reviews/<issue>/<agent-name>-<model-name>.json`. The
`triage-review` skill SHALL write its canonical combined inventory to
`{{path.documents}}Reviews/<issue>.json`. The workflow file's required `issue`
field SHALL name both paths. An empty value means there is no active workflow
issue; review dispatch and triage stop. Each source record SHALL identify its
producing agent, model, version, review target, and scope. Each finding SHALL
carry a stable identifier, version, P1-to-P6 priority, location, description,
analysis, and recommendation. The combined inventory SHALL retain references
to source findings together with their target and scope, and SHALL be the only
review record triage updates with the user's decision, variation, rationale,
action, and completion state.

#### Scenario: Record independent reviews

- **WHEN** workflow review obtains independent reviewer outputs
- **THEN** each reviewer SHALL write only its own
  `<agent-name>-<model-name>.json` source record below the shared review
  directory
- **AND** the coordinator SHALL determine the next version only for that exact
  source record without exposing another reviewer's findings or identity
- **AND** a reviewer SHALL NOT reuse, infer, or adopt identity components from
  another record
- **AND** workflow review SHALL not create or update the canonical combined
  inventory

#### Scenario: Record triage without implementation

- **WHEN** the user decides an item during `triage-items` triage
- **THEN** the agent SHALL update the corresponding item in the canonical
  combined JSON inventory with that decision and any variation or implementation
  guidance
- **AND** SHALL NOT implement the item while any item remains undecided

### Requirement: Workflow triage skill

The system SHALL serve `triage-review` as a packaged Guide skill for converting
independent review reports into a stable decision workflow.

#### Scenario: Collate every source report

- **WHEN** an agent selects `guide://$triage-review` for an active workflow
  issue and no canonical inventory exists
- **THEN** the skill SHALL read every valid source report in
  `{{path.documents}}Reviews/<issue>/`, irrespective of source agent or session
- **AND** SHALL preserve source-report agent-and-model identities, version,
  target, and scope in `{{path.documents}}Reviews/<issue>.json`
- **AND** SHALL deduplicate only findings describing the same underlying defect
- **AND** SHALL report the canonical inventory path before beginning decisions

#### Scenario: Incremental review triage

- **WHEN** a canonical inventory already exists and the user has not requested
  historical re-collation
- **THEN** the skill SHALL use its modification time as the cutoff
- **AND** SHALL consider only newer or updated source records
- **AND** SHALL preserve resolved findings as history and present only pending
  and newly collated findings for decisions

#### Scenario: Start sequential finding decisions

- **WHEN** workflow triage has written a complete, stable canonical inventory
- **THEN** it SHALL direct the agent to use `Guide skill "triage-items"`
- **AND** SHALL NOT implement, format, commit, push, discard changes, or take
  external action unless the user later explicitly authorises the specific
  follow-up
