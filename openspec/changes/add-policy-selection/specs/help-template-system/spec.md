## ADDED Requirements

### Requirement: Policy-Oriented User Documentation Structure

The system SHALL organize optional user-selectable operational preferences into a dedicated `policy` document category.

#### Scenario: Policy documents are grouped by topic
- **WHEN** policy guidance is added
- **THEN** it is stored under the `policy` category
- **AND** policy documents are organized by topic such as git, workflow, testing, tooling, or review posture

#### Scenario: Core guidance is made more neutral
- **WHEN** an existing user-facing document contains an optional preference rather than a universal rule
- **THEN** that preference is extracted into a policy document where practical
- **AND** the original core guidance is made more choice-agnostic

### Requirement: Policy Audit and Extraction

The system SHALL support extraction of embedded policy choices from existing user-facing templates and markdown documents.

#### Scenario: High-value topics are extracted first
- **WHEN** policy extraction is implemented
- **THEN** high-value topics such as scm, commit/pr behavior, workflow mode, testing, type checking, and toolchain preferences are prioritized
- **AND** additional policy topics discovered during the audit may also be extracted where they represent user-selectable preferences
