## ADDED Requirements

### Requirement: Positive profile detection and selection
The onboarding flow SHALL use inspection evidence to stage every compatible base-language, framework, aspect, platform, build, and test profile that it can positively identify. It SHALL obtain valid profile identifiers through `list_profiles` and retain user confirmation before application.

#### Scenario: Detect a composable Apple project stack
- **WHEN** inspection finds positive evidence for Swift, SwiftUI, iOS, and XCTest
- **THEN** onboarding SHALL stage `swift`, `swiftui`, `ios`, and `xctest` for confirmation
- **AND** it SHALL NOT replace an existing staged profile

#### Scenario: Ambiguous project marker
- **WHEN** inspection finds only a general Xcode project marker
- **THEN** onboarding MAY stage profiles established by that marker
- **AND** it SHALL NOT infer a specific Apple platform without target evidence
