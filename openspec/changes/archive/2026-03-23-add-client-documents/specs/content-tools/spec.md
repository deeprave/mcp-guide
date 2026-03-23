# Content Tools Specification

## MODIFIED Requirements

### Requirement: Client Document Queuing
The system SHALL queue uncached client document references before delivering category content.

#### Scenario: Queue uncached client documents
- **WHEN** `get_category_content` is called with client patterns
- **THEN** system identifies uncached client documents
- **AND** queues requests for missing documents

### Requirement: Client Path Validation on Request
The system SHALL validate client paths against `allowed_read_paths` before requesting documents.

#### Scenario: Request valid client document
- **WHEN** client document path is within `allowed_read_paths`
- **THEN** system requests document via `send_file_content`
- **AND** caches result

#### Scenario: Request invalid client document
- **WHEN** client document path is outside `allowed_read_paths`
- **THEN** request FAILS without calling `send_file_content`
- **AND** negative result is cached

### Requirement: Client Document Delivery
The system SHALL deliver all content (server and client) after fetching uncached client documents.

#### Scenario: Deliver mixed content
- **WHEN** all client documents are cached (positive or negative)
- **THEN** system delivers server documents
- **AND** delivers cached client documents
- **AND** excludes failed/missing client documents
