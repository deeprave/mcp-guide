## ADDED Requirements

### Requirement: Tool Description Standard for AI Agents
The system SHALL provide a standardized format for tool descriptions that enables AI agents to correctly understand and invoke tools without trial-and-error.

#### Scenario: Description structure
- **WHEN** a tool is documented
- **THEN** description includes four sections in order:
  1. Full description of purpose and use cases (markdown format)
  2. JSON Schema for arguments (code fence with type annotation)
  3. General usage instructions (marked as code)
  4. Concrete examples with explanations (marked as code)
- **AND** each section is clearly labeled

#### Scenario: Template availability
- **WHEN** developer creates new tool
- **THEN** `src/mcp_guide/tools/README.md` provides complete template
- **AND** template shows proper formatting for all four sections
- **AND** template includes example of Pydantic Field descriptions

#### Scenario: Tool module references
- **WHEN** tool module is created or updated
- **THEN** module includes comment pointing to README template
- **AND** comment appears near tool definition

#### Scenario: Complete field descriptions
- **WHEN** tool argument model is defined with Pydantic
- **THEN** every field includes `Field(description="...")` parameter
- **AND** description explains field purpose and valid values
- **AND** generated JSON Schema includes all field descriptions

#### Scenario: Schema presentation
- **WHEN** JSON Schema is included in tool description
- **THEN** schema is in code fence with appropriate type label
- **AND** schema shows complete Pydantic-generated structure
- **AND** schema is not open to interpretation

#### Scenario: Usage instructions clarity
- **WHEN** usage instructions are provided
- **THEN** instructions are marked as code for clarity
- **AND** instructions explain general patterns for tool invocation

#### Scenario: Example completeness
- **WHEN** examples are provided
- **THEN** examples include concrete values (not placeholders)
- **AND** each example includes explanation of what it demonstrates
- **AND** examples are marked as code
