# language-profiles Specification

## Purpose

Provide bundled, composable language, framework, extension, platform, and build
guidance profiles.

## Requirements

### Requirement: Additive language profiles
The system SHALL provide bundled, selectable language and template-syntax
profiles. Applying a profile SHALL add its focused guidance without removing
existing category selections.

#### Scenario: Apply a base-language profile
- **WHEN** a user applies a language profile
- **THEN** the project language category SHALL select that profile's guidance
- **AND** existing language selections SHALL remain

#### Scenario: Apply a template-language profile
- **WHEN** a user applies a documented template-language profile
- **THEN** the project language category SHALL select the corresponding
  template-language guidance
- **AND** existing language and framework selections SHALL remain

#### Scenario: Compose a template language with another profile
- **WHEN** a user applies a template-language profile together with a
  programming-language or framework profile
- **THEN** the project SHALL receive the guidance from every selected profile
- **AND** applying a selected profile again SHALL not duplicate selections

### Requirement: Additive framework and aspect profiles
The system SHALL provide bundled, selectable framework and aspect profiles.
Each profile SHALL add only its applicable focused guidance.

#### Scenario: Compose a language and extension profile
- **WHEN** a user applies a language and an aspect profile
- **THEN** the project SHALL receive guidance from both selections
- **AND** applying either profile again SHALL not duplicate selections

### Requirement: Platform profiles
The system SHALL provide bundled, selectable platform profiles. A platform
profile MAY select curated language-specific testing guidance where it is
normally relevant.

#### Scenario: Apply an Apple platform profile
- **WHEN** a user applies a platform profile
- **THEN** the project language category SHALL select that platform guidance
- **AND** existing categories and collections SHALL remain
