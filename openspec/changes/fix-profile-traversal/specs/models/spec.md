## ADDED Requirements

### Requirement: Safe Profile Identifiers

The system SHALL accept a profile identifier only when it is a simple basename of
one to 50 Unicode alphanumeric, underscore, or hyphen characters. The identifier
SHALL name the profile without a `.yaml` suffix. Internal basenames beginning with
an underscore, including `_default`, remain valid.

The system SHALL reject empty identifiers and identifiers containing a path
separator, backslash, period, whitespace, absolute-path marker, or any other
unsupported character before checking for a file or reading from the filesystem.

#### Scenario: Valid built-in and user profile basenames load
- **WHEN** a caller loads `_default`, `python`, or `team_profile-2`
- **THEN** the identifier passes validation
- **AND** profile loading continues using the corresponding `.yaml` file

#### Scenario: Traversal-style profile identifier is rejected before lookup
- **WHEN** a caller supplies `../outside`, `nested/profile`, `..\\outside`, an absolute path, or `profile.yaml`
- **THEN** profile loading fails as an invalid name
- **AND** the system does not perform an existence check or read for the supplied target

### Requirement: Canonically Contained Profile Files

Before reading a profile file, the system SHALL resolve the configured profiles
directory and the candidate `.yaml` file to canonical paths. The candidate's final
canonical target SHALL be contained by the canonical profiles directory. A target
outside that directory, including one reached through a symlink, SHALL be rejected
as an invalid profile source and SHALL NOT be read.

This containment rule SHALL apply to every profile load, including profile
inspection, profile application, profile filtering, and internal default-profile
loading.

#### Scenario: Escaping profile symlink is rejected
- **WHEN** a valid basename names a `.yaml` symlink in the profiles directory whose canonical target is outside that directory
- **THEN** profile loading fails as an invalid profile source
- **AND** the external YAML content is not read or returned

#### Scenario: Contained profile symlink remains usable
- **WHEN** a valid basename names a `.yaml` symlink whose canonical target remains inside the profiles directory
- **THEN** the profile loads normally
- **AND** its configuration is available to the caller

### Requirement: Safe Profile Load Failures

Profile-name and containment failures SHALL report a stable invalid-name failure
without disclosing the contents or canonical location of an external target. A
valid, contained basename whose file is absent SHALL continue to report a not-found
failure.

#### Scenario: Missing contained profile remains not found
- **WHEN** a valid simple profile basename has no corresponding contained `.yaml` file
- **THEN** the caller receives the existing not-found profile failure
- **AND** no external path is included in the failure
