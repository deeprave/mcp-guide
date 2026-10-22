# Spec Delta

## MODIFIED Requirements

### Requirement: Base-language profiles
The system SHALL provide bundled, selectable base-language profiles for C, Swift,
Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, Zig,
Jinja2, and Chevron. Each profile SHALL add focused guidance from the `lang`
category without removing existing category selections. Template-language
profiles SHALL be additive to programming-language, framework, platform, and
testing profiles.

#### Scenario: Apply a base-language profile
- **WHEN** a user applies the `swift` profile
- **THEN** the project language category SHALL select Swift guidance
- **AND** existing language selections SHALL remain

#### Scenario: Apply a template-language profile
- **WHEN** a user applies the `jinja2` or `chevron` profile
- **THEN** the project language category SHALL select the corresponding
  template-language guidance
- **AND** existing language and framework selections SHALL remain

#### Scenario: Compose a template language with another profile
- **WHEN** a user applies a template-language profile together with a
  programming-language or framework profile
- **THEN** the project SHALL receive the guidance from every selected profile
- **AND** applying a selected profile again SHALL not duplicate selections
