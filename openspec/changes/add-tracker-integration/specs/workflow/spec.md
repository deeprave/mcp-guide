## ADDED Requirements

### Requirement: Issue Resolution from External Tracker
When a tracker is configured, the workflow system SHALL resolve issue references against the external tracker and auto-populate workflow state fields.

#### Scenario: Issue resolved by ID
- **WHEN** `:workflow/issue <id>` is called and a tracker is configured
- **THEN** the system SHALL attempt to resolve `<id>` against the configured tracker
- **AND** on success SHALL populate `issue`, `tracking`, and `description` from the tracker response
- **AND** on failure SHALL fall back to treating the argument as a plain issue identifier

#### Scenario: Issue resolved by URL
- **WHEN** `:workflow/issue <url>` is called with a tracker URL
- **THEN** the system SHALL detect the tracker type from the URL
- **AND** resolve the issue and populate workflow state fields as above

#### Scenario: Tracker unavailable
- **WHEN** the tracker is configured but unreachable or times out
- **THEN** the workflow command SHALL complete using the manually supplied identifier
- **AND** the system SHALL surface a non-blocking informational message about the failure

#### Scenario: No tracker configured
- **WHEN** `:workflow/issue` is called and no tracker is configured
- **THEN** behaviour SHALL be identical to the current manual-entry behaviour

### Requirement: Tracker-Aware Queue Population
When a tracker is configured and the current issue is completed, the system SHALL optionally suggest open issues for the workflow queue.

#### Scenario: Queue suggestion on reset
- **WHEN** `:workflow/reset` completes and a tracker is configured
- **THEN** the system MAY suggest open issues from the tracker as candidates for `queue`
- **AND** SHALL NOT auto-populate `queue` without user acknowledgement when `workflow-consent` requires entry consent

#### Scenario: Queue population respects consent rules
- **WHEN** `workflow-consent` requires consent for queue changes
- **THEN** auto-population from tracker SHALL be presented as a suggestion requiring confirmation
- **AND** the user MAY decline without affecting the reset outcome

### Requirement: Tracker Context Variable
The template context SHALL expose tracker integration status for use in workflow templates.

#### Scenario: Tracker context when configured
- **WHEN** the `tracker` flag is set and credentials are available
- **THEN** `workflow.tracker` SHALL be available in template context
- **AND** SHALL contain at minimum: `type` (string) and `available` (boolean)

#### Scenario: Tracker context when not configured
- **WHEN** the `tracker` flag is absent
- **THEN** `workflow.tracker` SHALL be falsy or absent from template context
