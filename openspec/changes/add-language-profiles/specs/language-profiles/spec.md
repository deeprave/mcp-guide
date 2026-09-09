## Purpose

Provide bundled Swift and Objective-C language profiles and guidance so Apple-language projects can be configured through the same additive profile mechanism as Python, Kotlin, and other existing languages.

## ADDED Requirements

### Requirement: Swift language profile
The system SHALL provide a bundled `swift` profile that adds Swift language guidance to the project's language category.

#### Scenario: Apply the Swift profile
- **WHEN** a user applies the `swift` profile
- **THEN** the project language category SHALL select Swift guidance
- **AND** the guidance SHALL cover current Swift conventions that apply across Apple platforms

### Requirement: Objective-C language profile
The system SHALL provide a bundled `objective-c` profile that adds Objective-C language guidance to the project's language category.

#### Scenario: Apply the Objective-C profile
- **WHEN** a user applies the `objective-c` profile
- **THEN** the project language category SHALL select Objective-C guidance
- **AND** existing language selections SHALL remain

### Requirement: Language and platform profiles compose
Applying a language profile and an Apple platform profile together SHALL combine both sets of guidance.

#### Scenario: Swift and iOS compose
- **WHEN** a user applies `swift` and then `ios`
- **THEN** the project SHALL receive both Swift language guidance and iOS platform guidance
- **AND** applying either profile again SHALL not duplicate those selections
