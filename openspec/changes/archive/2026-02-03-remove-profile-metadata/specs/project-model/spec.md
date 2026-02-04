## REMOVED Requirements

### Requirement: Profile Metadata Tracking
The Project model SHALL NOT track applied profile names in metadata.

#### Scenario: No metadata field
- **WHEN** a Project is created
- **THEN** it does not have a metadata field
- **AND** profile application does not record profile names

#### Scenario: Profile effects only
- **WHEN** a profile is applied to a project
- **THEN** only the profile's categories and collections are added
- **AND** no metadata about the profile application is stored
