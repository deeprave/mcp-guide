## ADDED Requirements

### Requirement: Analytics Feature Flag
The system SHALL support an `analytics` feature flag that enables local content access recording on an opt-in basis.

#### Scenario: Analytics disabled by default
- **WHEN** the `analytics` flag is not set
- **THEN** no content access events SHALL be recorded
- **AND** content delivery performance SHALL be unaffected

#### Scenario: Analytics enabled
- **WHEN** the `analytics` flag is set to true
- **THEN** the system SHALL record an access event for each document delivered to an agent

#### Scenario: Analytics path configuration
- **WHEN** the `analytics-path` flag is set
- **THEN** the system SHALL write events to the specified path
- **AND** the path SHALL be validated against `allowed_write_paths` security policy

#### Scenario: Analytics path default
- **WHEN** `analytics-path` is not set and analytics is enabled
- **THEN** the system SHALL default to `.guide/analytics.jsonl` relative to the project root

### Requirement: Content Access Event Recording
When analytics is enabled, the system SHALL record a structured event for each document served.

#### Scenario: Event written per document
- **WHEN** a document is delivered to an agent
- **THEN** an event SHALL be appended to the analytics log containing: timestamp (ISO 8601), session identifier, document path, category, and collection (or null)

#### Scenario: Write errors do not affect delivery
- **WHEN** the analytics log cannot be written (permissions, disk full, etc.)
- **THEN** the content delivery SHALL complete successfully
- **AND** the write failure SHALL be suppressed without surfacing an error to the agent

#### Scenario: Events are append-only
- **WHEN** new events are recorded
- **THEN** they SHALL be appended to the existing log file
- **AND** existing events SHALL NOT be modified or deleted by the recording process

### Requirement: Stats Command
The system SHALL provide a `:stats` prompt command that aggregates and displays content access data from the local analytics log.

#### Scenario: Most-accessed documents
- **WHEN** `:stats` is invoked
- **THEN** the system SHALL display the most-accessed documents ranked by access count

#### Scenario: Per-category breakdown
- **WHEN** `:stats` is invoked
- **THEN** the system SHALL display access counts grouped by category

#### Scenario: Never-accessed documents
- **WHEN** `:stats` is invoked
- **THEN** the system SHALL identify documents present in the project but absent from the analytics log
- **AND** list them as candidates for review or removal

#### Scenario: Filtered by recency
- **WHEN** `:stats --since <n>` is invoked with a session count or date
- **THEN** the system SHALL restrict aggregation to events within the specified window

#### Scenario: No analytics data available
- **WHEN** `:stats` is invoked but analytics has not been enabled or the log is empty
- **THEN** the system SHALL display a clear message explaining that analytics is not enabled or no data has been recorded yet

### Requirement: Analytics Data Privacy
Analytics data SHALL remain strictly local and SHALL NOT be transmitted outside the user's machine.

#### Scenario: No network calls from analytics
- **WHEN** analytics is enabled and events are recorded
- **THEN** no network requests SHALL be made by the analytics subsystem

#### Scenario: Analytics log location is user-controlled
- **WHEN** the analytics log path is resolved
- **THEN** it SHALL always be within the project filesystem
- **AND** SHALL be subject to `allowed_write_paths` validation
