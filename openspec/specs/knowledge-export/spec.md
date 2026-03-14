# knowledge-export Specification

## Purpose
TBD - created by archiving change add-knowledge-export. Update Purpose after archive.
## Requirements
### Requirement: export_content Tool
The system SHALL provide an `export_content` tool that returns content with an instruction for the agent to write it to a specified path for knowledge indexing.

#### Scenario: Valid path export
- **WHEN** `export_content` is called with a valid expression and a path within `allowed_write_paths`
- **THEN** content is resolved using the same logic as `get_content`
- **AND** full content is returned
- **AND** the result includes an instruction directing the agent to write the content to the specified path

#### Scenario: Force overwrite
- **WHEN** `export_content` is called with `force=True`
- **THEN** the instruction permits the agent to overwrite an existing file at the path

#### Scenario: Create only (default)
- **WHEN** `export_content` is called with `force=False` (default)
- **THEN** the instruction directs the agent to write the file only if it does not already exist

#### Scenario: Path not in allowed_write_paths
- **WHEN** `export_content` is called with a path not in the project's `allowed_write_paths`
- **THEN** content is NOT returned
- **AND** Result.failure is returned with error_type "permission_denied"
- **AND** instruction indicates the path must be added to `allowed_write_paths` first

