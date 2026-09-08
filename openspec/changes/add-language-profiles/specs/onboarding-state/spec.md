## ADDED Requirements

### Requirement: Apple, language, and test profile selection
The onboarding flow SHALL offer the new Apple platform, Swift, Objective-C, and test-stack profiles where it already offers language or technology profile choices. Inspection SHALL treat Xcode, Swift package, and Apple project markers as evidence for those profiles. iPadOS SHALL stage the `ios` profile.

#### Scenario: Select Swift and iOS during onboarding
- **WHEN** a user identifies Swift and iOS as used by the project
- **THEN** onboarding SHALL stage the `swift` and `ios` profiles for confirmation

#### Scenario: Infer Apple markers from the repository
- **WHEN** onboarding inspection finds Apple project markers such as an Xcode project or Swift package manifest
- **THEN** onboarding SHALL propose the matching language, platform, and test-stack profiles where those can be inferred

#### Scenario: Select a test-stack profile during onboarding
- **WHEN** a user identifies XCTest or Swift Testing as the project test stack
- **THEN** onboarding SHALL stage the corresponding test profile for confirmation
