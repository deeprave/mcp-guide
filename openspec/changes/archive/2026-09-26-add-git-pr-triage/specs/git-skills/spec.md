# Spec Delta

## MODIFIED Requirements

### Requirement: Git skills are independently available
The system SHALL provide `git-commit`, `git-push`, `git-pr`, `git-sync`, and
`git-pr-triage` as bundled Guide skill packages. Their discovery and rendering
SHALL NOT require workflow or OpenSpec features. Instructions that refer to
optional features SHALL be conditional on those features.

#### Scenario: Features are disabled
- **WHEN** workflow and OpenSpec features are disabled
- **THEN** each Git skill remains available without feature-specific instructions
