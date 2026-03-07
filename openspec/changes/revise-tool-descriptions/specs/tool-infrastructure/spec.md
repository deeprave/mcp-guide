## MODIFIED Requirements

### Requirement: Tool Description Standard for AI Agents
The system SHALL provide a standardized format for tool descriptions that enables AI agents to correctly understand and invoke tools without trial-and-error.

#### Scenario: Description structure
- **WHEN** a tool is documented
- **THEN** the docstring on the registered tool function contains a concise description (1-5 sentences)
- **AND** the description covers purpose, key behaviours, and any non-obvious constraints
- **AND** JSON Schema is NOT included in the docstring (auto-generated from Pydantic models by `build_description`)
- **AND** Usage Instructions and Concrete Examples sections are optional, used only for tools with complex or non-obvious invocation patterns

#### Scenario: Auto-generated arguments appended
- **WHEN** a tool is registered via `@toolfunc`
- **THEN** `build_description` appends a `## Arguments` block generated from Pydantic field descriptions
- **AND** the combined description (docstring + arguments) is registered with FastMCP

#### Scenario: Template availability
- **WHEN** developer creates new tool
- **THEN** `src/mcp_guide/tools/README.md` provides the concise description standard
- **AND** template shows correct docstring placement on the registered function (not `internal_*`)
- **AND** template includes example of Pydantic Field descriptions

#### Scenario: Docstring placement
- **WHEN** a tool has an `internal_*` implementation function
- **THEN** the agent-facing docstring is on the registered `@toolfunc` function
- **AND** the `internal_*` function may have a minimal or no docstring

#### Scenario: Complete field descriptions
- **WHEN** tool argument model is defined with Pydantic
- **THEN** every field includes `Field(description="...")` parameter
- **AND** description explains field purpose and valid values
- **AND** generated `## Arguments` block includes all field descriptions
