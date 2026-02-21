## ADDED Requirements

### Requirement: MkDocs Site Generation
The system SHALL provide MkDocs configuration for generating a static documentation site.

#### Scenario: MkDocs configuration
- **WHEN** mkdocs.yml exists in project root
- **THEN** it defines site name and description
- **AND** it configures Material theme
- **AND** it maps navigation to docs/user/ content
- **AND** it sets docs_dir to docs/

#### Scenario: Local preview
- **WHEN** developer runs mkdocs serve
- **THEN** documentation site is available at localhost:8000
- **AND** changes auto-reload during development
- **AND** all navigation links work correctly

#### Scenario: Static site build
- **WHEN** mkdocs build is executed
- **THEN** static site is generated in site/ directory
- **AND** site/ is excluded from version control
- **AND** generated site is ready for deployment
