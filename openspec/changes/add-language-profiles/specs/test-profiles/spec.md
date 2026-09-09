## Purpose

Provide bundled test-stack profiles so a project can select generic testing checks and Apple test frameworks without changing the existing testing-policy dimension.

## ADDED Requirements

### Requirement: Generic testing profile
The system SHALL provide a bundled `testing` profile that selects the existing general testing check guidance.

#### Scenario: Apply the testing profile
- **WHEN** a user applies the `testing` profile
- **THEN** the project checks category SHALL select the existing testing check guidance
- **AND** testing-policy selections SHALL remain unchanged

### Requirement: XCTest profile
The system SHALL provide a bundled `xctest` profile that adds XCTest guidance.

#### Scenario: Apply the XCTest profile
- **WHEN** a user applies the `xctest` profile
- **THEN** the project SHALL receive XCTest guidance
- **AND** existing categories and collections SHALL remain

### Requirement: Swift Testing profile
The system SHALL provide a bundled `swift-testing` profile that adds Swift Testing framework guidance.

#### Scenario: Apply the Swift Testing profile
- **WHEN** a user applies the `swift-testing` profile
- **THEN** the project SHALL receive Swift Testing guidance
- **AND** applying `xctest` as well SHALL keep both test-stack selections
