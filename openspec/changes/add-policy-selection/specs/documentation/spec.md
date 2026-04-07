## MODIFIED Requirements

### Requirement: Profiles Documentation
The system SHALL provide accurate user documentation for profiles that reflects
the current set of available profiles.

#### Scenario: Profiles documentation content
- **WHEN** a user reads the profiles documentation
- **THEN** it does not reference methodology profiles (tdd, bdd, yagni, solid)
  that have been superseded by policy selection
- **AND** it directs users to the policies documentation for methodology
  preference configuration
- **AND** all profile examples reference profiles that actually exist

### Requirement: Guide Category Documentation
The system SHALL provide accurate user documentation for the guide category
content that reflects the current set of guide documents.

#### Scenario: Guide category file listing
- **WHEN** a user reads the guide category documentation
- **THEN** it does not list methodology documents (tdd, bdd, yagni, solid, ddd)
  that have been removed from the guide category
- **AND** it reflects that methodology content is now injected via the
  methodology policy partial
