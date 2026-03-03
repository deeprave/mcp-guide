## MODIFIED Requirements

### Requirement: Smart Update Logic
The system SHALL provide `update_documents()` function (renamed from `update_templates()`) that updates all documentation files using smart comparison logic.

#### Scenario: Function renamed for clarity
- **WHEN** update logic is invoked
- **THEN** function is named `update_documents()`
- **AND** handles all file types (templates, markdown, etc.)
- **AND** uses same smart update logic as before

#### Scenario: Docroot ensured before operations
- **WHEN** `install_templates()` or `update_documents()` is called
- **THEN** `await AsyncPath(docroot).mkdir(parents=True, exist_ok=True)` is called first
- **AND** docroot is guaranteed to exist before any file operations
- **AND** lock file creation cannot fail due to missing directory

#### Scenario: Reused by update tool
- **WHEN** `update_documents` tool is invoked
- **THEN** it calls `update_documents()` function
- **AND** uses same parameters as `mcp-install update`
- **AND** returns same statistics format

## ADDED Requirements

### Requirement: Docroot Safety Check
The system SHALL prevent updates when docroot resolves to the same path as the template source directory.

#### Scenario: Docroot is template source
- **WHEN** update is initiated
- **AND** `docroot.resolve(strict=True)` equals template source path
- **THEN** exception is raised
- **AND** error message states "docroot cannot be same as template source"
- **AND** no files are modified

#### Scenario: Docroot is safe
- **WHEN** update is initiated
- **AND** `docroot.resolve(strict=True)` differs from template source path
- **THEN** update proceeds normally

### Requirement: Version Comparison Logic
The system SHALL compare `.version` file content with current package version to determine if update is needed.

#### Scenario: Version file exists and differs
- **WHEN** `.version` file exists in docroot
- **AND** content differs from `__version__`
- **THEN** update is needed

#### Scenario: Version file missing
- **WHEN** `.version` file does not exist in docroot
- **THEN** update is needed (treat as old installation)

#### Scenario: Version file matches
- **WHEN** `.version` file exists in docroot
- **AND** content matches `__version__`
- **THEN** update is not needed
