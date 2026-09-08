## Purpose

Provide bundled, composable profiles and guidance for Apple platform projects so agents can select iOS, macOS, watchOS, tvOS, or visionOS the same way they select existing language profiles.

## ADDED Requirements

### Requirement: Apple platform profiles
The system SHALL provide bundled profiles named `ios`, `macos`, `watchos`, `tvos`, and `visionos`. Each profile SHALL add Apple platform guidance to the project's language category without removing existing categories or collections. iPadOS SHALL use the `ios` profile.

#### Scenario: Apply an Apple platform profile
- **WHEN** a user applies the `ios` profile
- **THEN** the project language category SHALL select iOS platform guidance
- **AND** existing categories and collections SHALL remain

#### Scenario: Remaining Apple platforms are selectable
- **WHEN** a user applies `macos`, `watchos`, `tvos`, or `visionos`
- **THEN** the project language category SHALL select the matching platform guidance
- **AND** applying a second Apple platform profile SHALL add that guidance without replacing the first

#### Scenario: iPadOS uses the iOS profile
- **WHEN** a user or onboarding flow identifies an iPadOS project
- **THEN** the `ios` profile SHALL be used
- **AND** no separate `ipados` profile SHALL be required
