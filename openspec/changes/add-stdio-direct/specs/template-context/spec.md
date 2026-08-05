## ADDED Requirements

### Requirement: Filesystem source-aware rendering
The template rendering context SHALL expose whether supported workflow and OpenSpec data is available through confirmed direct filesystem access.

#### Scenario: Confirmed direct source
- **WHEN** direct filesystem access is confirmed and current data was read successfully
- **THEN** templates SHALL be able to render guidance without requesting relay of that data

#### Scenario: Relay source
- **WHEN** direct filesystem access is not confirmed or direct data is unavailable
- **THEN** templates SHALL retain existing relay guidance where it is otherwise required
