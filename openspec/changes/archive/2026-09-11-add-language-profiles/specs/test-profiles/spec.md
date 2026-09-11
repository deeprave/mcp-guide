## Purpose

Provide testing and verification profiles and documents that compose with language and platform profiles while keeping build guidance out of the checks category.

## ADDED Requirements

### Requirement: Generic testing profile
The system SHALL provide a bundled, selectable `testing` profile that selects the existing general testing guidance from the `checks` category.

#### Scenario: Apply generic testing guidance
- **WHEN** a user applies the `testing` profile
- **THEN** the project checks category SHALL select the existing general testing guidance
- **AND** existing testing and policy selections SHALL remain

### Requirement: Platform-specific testing guidance
The system SHALL provide focused testing guidance under `checks/<language>/<platform>/` for supported language/platform combinations. Shared framework guidance MAY be grouped where doing so avoids repetition.

#### Scenario: Select platform testing guidance
- **WHEN** a user applies compatible Swift and iOS profiles
- **THEN** the project SHALL select iOS-specific Swift testing guidance from the `checks` category
- **AND** that guidance SHALL remain separate from `lang/build/` guidance

### Requirement: Apple testing framework profiles
The system SHALL provide bundled, selectable `xctest` and `swift-testing` profiles with focused test-framework guidance. Applying both SHALL preserve both sets of guidance.

#### Scenario: Compose Apple test frameworks
- **WHEN** a user applies `xctest` and `swift-testing`
- **THEN** the project SHALL receive both framework guidance selections
- **AND** applying either profile again SHALL not duplicate selections
