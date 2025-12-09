## MODIFIED Requirements

### Requirement: Tool Naming Convention
The system SHALL use consistent, concise tool names without unnecessary prefixes.

#### Scenario: Category content tool naming
- **WHEN** retrieving category content
- **THEN** tool is named `category_content` (not `get_category_content`)

#### Scenario: Collection content tool naming
- **WHEN** retrieving collection content
- **THEN** tool is named `collection_content` (not `get_collection_content`)

#### Scenario: Client info tool naming
- **WHEN** retrieving client information
- **THEN** tool is named `client_info` (not `get_client_info`)

#### Scenario: Project retrieval tool naming
- **WHEN** retrieving current project
- **THEN** tool is named `get_project` (not `get_current_project`)

#### Scenario: Project setting tool naming
- **WHEN** setting current project
- **THEN** tool is named `set_project` (not `set_current_project`)

#### Scenario: Backward compatibility
- **WHEN** old tool names are used
- **THEN** tools are not found (breaking change)
- **AND** clear error message indicates tool does not exist
