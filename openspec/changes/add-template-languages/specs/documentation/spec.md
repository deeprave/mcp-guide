# Spec Delta

## MODIFIED Requirements

### Requirement: Expanded profile catalogue documentation
User documentation for profiles SHALL describe the composable base-language,
template-language, extension/framework, platform, and test-stack model. It
SHALL distinguish `lang/` language and template-language guidance, `lang/build/`
build guidance, and `checks/` testing guidance, and name only profiles that
exist.

#### Scenario: Profiles documentation explains composition
- **WHEN** a user reads the profiles documentation
- **THEN** it SHALL show a valid composed selection such as `swift`, `swiftui`,
  `ios`, and `xctest`
- **AND** it SHALL explain that these profiles add guidance rather than replacing
  one another

#### Scenario: Profiles documentation names template languages
- **WHEN** a user reads the profiles documentation
- **THEN** it SHALL identify the available `jinja2` and `chevron`
  template-language profiles
- **AND** it SHALL explain that either can be combined with the project’s
  programming-language and framework profiles
