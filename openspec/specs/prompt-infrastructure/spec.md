# prompt-infrastructure Specification

## Purpose
TBD - created by archiving change add-guide-prompt. Update Purpose after archive.
## Requirements
### Requirement: PromptArguments Protocol (COMPLETED)
The system SHALL provide a PromptArguments protocol in mcp_core for prompt argument validation.

#### Scenario: PromptArguments protocol definition (COMPLETED)
- **WHEN** prompt arguments need type safety
- **THEN** PromptArguments protocol provides base interface
- **AND** follows same patterns as ToolArguments

#### Scenario: GuidePromptArguments implementation (COMPLETED)
- **WHEN** guide prompt needs argument structure
- **THEN** GuidePromptArguments implements PromptArguments
- **AND** provides command: Optional[str] field
- **AND** provides arguments: List[str] field

#### Scenario: Prompt schema generation (COMPLETED)
- **WHEN** prompt decorator processes PromptArguments class
- **THEN** automatically generates JSON schema for FastMCP
- **AND** agents receive schema information for proper invocation

### Requirement: Prompt Decorator Infrastructure (COMPLETED)
The system SHALL provide prompt decorator infrastructure for FastMCP prompt registration.

#### Scenario: Prompt decorator creation (COMPLETED)
- **WHEN** prompt functions need registration
- **THEN** prompt decorator handles FastMCP registration
- **AND** supports argument validation and schema generation

#### Scenario: Prompt proxy pattern (COMPLETED)
- **WHEN** server initialization needs deferred prompt registration
- **THEN** prompt proxy pattern allows import-time decoration
- **AND** actual registration happens after server creation

### Requirement: Prompt Prefix Support (COMPLETED)
The system SHALL provide configurable prompt prefixes to avoid name collisions.

#### Scenario: Default prompt prefix behavior (COMPLETED)
- **WHEN** MCP_PROMPT_PREFIX environment variable is not set
- **THEN** prompts use no prefix (empty string)
- **AND** prompt names are registered as-is

#### Scenario: Custom prompt prefix (COMPLETED)
- **WHEN** MCP_PROMPT_PREFIX environment variable is set to "custom"
- **THEN** prompts are registered with "custom_" prefix
- **AND** "guide" prompt becomes "custom_guide"

#### Scenario: Prompt prefix configuration (COMPLETED)
- **WHEN** prompt decorator initializes
- **THEN** reads prefix from MCP_PROMPT_PREFIX environment variable
- **AND** defaults to empty string if not set

---

### Requirement: Space-Separated Flag Values
The command parser SHALL support space-separated flag values (`--flag value`) for flags declared in frontmatter `kwargs.argrequired`.

#### Scenario: Flag with equals syntax
- **WHEN** parsing `--tracking=GUIDE-177` where `tracking` is in `argrequired`
- **THEN** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** behavior is unchanged from current implementation

#### Scenario: Flag with space-separated syntax
- **WHEN** parsing `--tracking GUIDE-177` where `tracking` is in `argrequired`
- **THEN** parser SHALL consume next argument as the flag value
- **AND** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** `"GUIDE-177"` SHALL NOT appear in positional args

#### Scenario: Flag without value when required
- **WHEN** parsing `--tracking` where `tracking` is in `argrequired`
- **AND** no value follows (end of arguments or next token starts with `-`)
- **THEN** parser SHALL add error: `"Flag --tracking requires a value"`
- **AND** `kwargs["tracking"]` SHALL NOT be set

#### Scenario: Flag not in argrequired list
- **WHEN** parsing `--verbose` where `verbose` is NOT in `argrequired`
- **THEN** parser SHALL treat it as boolean flag
- **AND** `kwargs["verbose"]` SHALL equal `True`
- **AND** behavior is unchanged from current implementation

#### Scenario: Multiple required flags
- **WHEN** parsing `--tracking GUIDE-177 --issue fix-bug --verbose`
- **AND** `tracking` and `issue` are in `argrequired`
- **THEN** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** `kwargs["issue"]` SHALL equal `"fix-bug"`
- **AND** `kwargs["verbose"]` SHALL equal `True`

#### Scenario: Required flag followed by another flag
- **WHEN** parsing `--tracking --verbose` where `tracking` is in `argrequired`
- **THEN** parser SHALL add error: `"Flag --tracking requires a value"`
- **AND** `kwargs["tracking"]` SHALL NOT be set
- **AND** `kwargs["verbose"]` SHALL equal `True`

### Requirement: Frontmatter-Driven Argument Requirements
The command parser SHALL accept `argrequired` list from frontmatter to determine which flags require values.

#### Scenario: Parser receives argrequired list
- **WHEN** `parse_command_arguments()` is called with `argrequired=["tracking", "issue"]`
- **THEN** parser SHALL use this list to determine flag value requirements
- **AND** flags in list SHALL consume next argument as value when no `=` present

#### Scenario: Parser without argrequired list
- **WHEN** `parse_command_arguments()` is called without `argrequired` parameter
- **THEN** parser SHALL use current behavior for all flags
- **AND** backward compatibility is maintained

#### Scenario: Empty argrequired list
- **WHEN** `parse_command_arguments()` is called with `argrequired=[]`
- **THEN** parser SHALL treat all flags as boolean
- **AND** behavior matches current implementation

