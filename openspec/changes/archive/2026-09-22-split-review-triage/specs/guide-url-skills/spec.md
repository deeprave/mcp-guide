## MODIFIED Requirements

### Requirement: Workflow review skill
The system SHALL serve `workflow-review` as a packaged Guide skill for independent code review. It SHALL transition the configured workflow file to the review phase when workflow mode is active, and SHALL validate the active OpenSpec change when OpenSpec mode is active. After producing its independent source reports, it SHALL report their paths and request the user's next action without collating or triaging them.

#### Scenario: Choose a review target when mode is omitted
- **WHEN** an agent selects `guide://$workflow-review` without a `mode` query parameter through either the native resource or the `read_resource` tool
- **THEN** its declared `review-target` form SHALL offer mutually exclusive choices for uncommitted work, `main`, a named branch, and a pull request URL or number
- **AND** when that form is unavailable or cancelled, the skill SHALL direct the agent to present mutually exclusive client-native choices for uncommitted work, `main`, a named branch, and a pull request URL or number
- **AND** SHALL direct the agent to use the same choices as a numbered list when the client cannot render a choice picker
- **AND** SHALL direct the agent not to begin review until the user selects a target
- **AND** SHALL instruct it to read the configured workflow file before changing its phase to `review` when workflow mode is active

#### Scenario: Select a review target
- **WHEN** an agent selects `guide://$workflow-review` with `mode` equal to `uncommitted`, `main`, a branch name, a pull-request URL, or a pull-request number for the current repository
- **THEN** the skill SHALL direct it to review that selected target
- **AND** SHALL preserve the query value through the shared Guide template keyword context

#### Scenario: Obtain independent review coverage
- **WHEN** workflow review begins
- **THEN** the skill SHALL direct the agent to obtain two independent reviews
- **AND** one SHALL use the heavier available model at medium or high effort
- **AND** the other SHALL use a different lighter available model at its highest supported effort when possible
- **AND** they SHALL run concurrently in isolated subprocesses when that execution mechanism is supported
- **AND** each reviewer SHALL receive only the selected target, relevant repository evidence, governing repository guidance, applicable OpenSpec artefacts, and the required report format
- **AND** neither reviewer SHALL receive or account for prior conversation, previous reviews, existing review records, collated inventories, or the other reviewer's findings
- **AND** after both reports are written, the coordinator SHALL report their paths and ask the user what to do next
- **AND** SHALL NOT collate reports, inspect pull-request comments, create a canonical inventory, or invoke `just-one`

#### Scenario: Account for existing pull-request comments after independent review
- **WHEN** the selected target is a pull request with existing review comments
- **THEN** workflow review SHALL leave those comments for workflow triage to inspect after it creates the canonical inventory
- **AND** SHALL NOT expose those comments to the independent reviewers or modify their source reports

#### Scenario: Validate the active OpenSpec change
- **WHEN** OpenSpec mode is active for a workflow review
- **THEN** the skill SHALL direct the agent to run strict validation for the active change before completing the review

## ADDED Requirements

### Requirement: Workflow triage skill
The system SHALL serve `workflow-triage` as a packaged Guide skill for converting independent review reports into a stable decision workflow.

#### Scenario: Collate every source report
- **WHEN** an agent selects `guide://$workflow-triage` for an active workflow issue
- **THEN** the skill SHALL read every valid source report in `{{path.documents}}Reviews/<issue>/`
- **AND** SHALL preserve each source report reference, version, target, and scope in `{{path.documents}}Reviews/<issue>.json`
- **AND** SHALL deduplicate only findings describing the same underlying defect
- **AND** SHALL record target and scope on a combined finding when its source reports agree, or retain that context on each source reference when they differ
- **AND** SHALL preserve existing triage decisions for matching combined findings
- **AND** SHALL report the canonical inventory path before beginning user decisions

#### Scenario: Start sequential finding decisions
- **WHEN** workflow triage has written a complete, stable canonical inventory
- **THEN** it SHALL direct the agent to use `Guide skill "just-one"`
- **AND** SHALL NOT implement, format, commit, push, or discard changes unless the user later explicitly confirms the collected accepted actions

## MODIFIED Requirements

### Requirement: Durable review finding records
The workflow review skill SHALL record each independent review in `{{path.documents}}Reviews/<issue>/<agent-name>.json`. The workflow triage skill SHALL write its canonical combined inventory to `{{path.documents}}Reviews/<issue>.json`. The workflow file's required `issue` field SHALL name both paths. An empty value means there is no active workflow issue; review dispatch and triage stop. Each source record SHALL identify its reviewer, version, review target, and scope, and each finding SHALL carry a stable identifier, version, P1-to-P6 priority, location, description, analysis, and recommendation. The combined inventory SHALL retain references to the source findings together with their target and scope, and SHALL be the only review record triage updates with the user's decision, variation, rationale, action, and completion state.

#### Scenario: Record independent reviews
- **WHEN** workflow review obtains independent reviewer outputs
- **THEN** each reviewer SHALL write its own JSON record below the shared review directory
- **AND** before dispatch the coordinator SHALL determine each reviewer's next positive version without exposing its earlier findings
- **AND** a reviewer SHALL overwrite only its own prior record and SHALL assign its current version to every finding it writes
- **AND** one reviewer SHALL NOT overwrite another reviewer's record
- **AND** a reviewer SHALL NOT load, merge, or update adjacent review records while producing its own report
- **AND** workflow review SHALL not create or update the canonical combined inventory

#### Scenario: Record triage without implementation
- **WHEN** the user decides a finding during `just-one` triage
- **THEN** the agent SHALL update the corresponding finding in the canonical combined JSON inventory with that decision and any variation or implementation guidance
- **AND** SHALL NOT implement the finding while any finding remains undecided
