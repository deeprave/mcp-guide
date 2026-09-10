## ADDED Requirements

### Requirement: Expanded profile catalogue documentation
User documentation for profiles SHALL describe the composable base-language, extension/framework, platform, and test-stack model. It SHALL distinguish `lang/` language guidance, `lang/build/` build guidance, and `checks/` testing guidance, and name only profiles that exist.

#### Scenario: Profiles documentation explains composition
- **WHEN** a user reads the profiles documentation
- **THEN** it SHALL show a valid composed selection such as `swift`, `swiftui`, `ios`, and `xctest`
- **AND** it SHALL explain that these profiles add guidance rather than replacing one another
