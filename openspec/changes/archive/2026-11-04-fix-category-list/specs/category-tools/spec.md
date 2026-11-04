# Spec Delta

## MODIFIED Requirements

### Requirement: category_list_files Tool

The system SHALL provide a `category_list_files` tool that lists all files in a category directory.

The tool SHALL accept an optional `source` filter parameter to control which entries are returned:
- `files` — filesystem files only (current behaviour)
- `stored` — stored documents only
- No filter (default) — both filesystem files and stored documents

Each entry in the response SHALL indicate its source (`file` or `store`).

A category that has no directory in the docroot SHALL be listed normally, as a category with no filesystem files; the absence of the directory SHALL NOT be reported as an error.

#### Scenario: List all sources (default)
- **WHEN** `category_list_files` is called without a source filter
- **THEN** output includes both filesystem files and stored documents
- **AND** each entry indicates its source

#### Scenario: List filesystem files only
- **WHEN** `category_list_files` is called with source filter `files`
- **THEN** only filesystem files are returned

#### Scenario: List stored documents only
- **WHEN** `category_list_files` is called with source filter `stored`
- **THEN** only stored documents are returned

#### Scenario: No stored documents exist
- **WHEN** `category_list_files` is called for a category with no stored documents
- **THEN** behaviour is unchanged — only filesystem files are listed

#### Scenario: Category without a docroot directory, default source
- **WHEN** `category_list_files` is called without a source filter for a category that exists in configuration and the store but has no directory in the docroot
- **THEN** the stored documents are returned
- **AND** the call succeeds

#### Scenario: Category without a docroot directory, files source
- **WHEN** `category_list_files` is called with source filter `files` for a category that has no directory in the docroot
- **THEN** an empty list is returned
- **AND** the call succeeds

#### Scenario: Category without directory or stored documents
- **WHEN** `category_list_files` is called without a source filter for a category that has no directory and no stored documents
- **THEN** an empty list is returned
