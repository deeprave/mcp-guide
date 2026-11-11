# Spec Delta

## MODIFIED Requirements

### Requirement: Cache State Management
The system SHALL maintain cache state for an OpenSpec changes list, including its acquisition time and refresh generation. Cache validity SHALL be determined by its TTL or an explicit refresh, not client-observed filesystem metadata.

#### Scenario: Initialize cache state
- **GIVEN** a new OpenSpecTask instance
- **WHEN** the task is initialised
- **THEN** changes data, timestamp, and refresh generation SHALL be unset

#### Scenario: Cache valid data
- **GIVEN** cached changes data exists
- **AND** its timestamp is less than one hour old
- **WHEN** get_changes() is called
- **THEN** the cached changes list SHALL be returned

#### Scenario: Cache expired data
- **GIVEN** cached changes data exists
- **AND** its timestamp is at least one hour old
- **WHEN** get_changes() is called
- **THEN** the cached changes list SHALL become unavailable
- **AND** a later OpenSpec-list render SHALL request a refreshed list

#### Scenario: Missing or changed directory metadata
- **GIVEN** cached changes data exists
- **WHEN** a consumer requests a forced refresh
- **THEN** the OpenSpec-list render SHALL request a new OpenSpec-list result
- **AND** SHALL not inspect or request a changes-directory modification time

#### Scenario: Superseded refresh response
- **GIVEN** a changes refresh has been superseded by a newer refresh
- **WHEN** an OpenSpec-list response for the older refresh arrives
- **THEN** the system SHALL ignore that response
- **AND** SHALL NOT associate its changes data with the newer refresh generation
