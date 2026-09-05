# tool-infrastructure Specification

## Purpose
TBD - created by archiving change tool-conventions. Update Purpose after archive.

## Requirements

### Requirement: Result Pattern Implementation
The system SHALL provide a Result[T] generic type in mcp_core for tool responses.

#### Scenario: Success result creation
- **WHEN** a tool succeeds
- **THEN** Result.ok(value) creates success result with value
- **AND** success field is True
- **AND** optional message and instruction fields can be included

#### Scenario: Failure result creation
- **WHEN** a tool fails
- **THEN** Result.failure(error, error_type) creates failure result
- **AND** success field is False
- **AND** error and error_type fields are populated
- **AND** optional exception, message, and instruction fields can be included

#### Scenario: JSON serialization
- **WHEN** Result.to_json_str() is called
- **THEN** returns JSON string suitable for MCP tool response
- **AND** exception field is converted to exception_type and exception_message
- **AND** all optional fields are included if present

#### Scenario: Instruction field for agent guidance
- **WHEN** Result includes instruction field
- **THEN** instruction guides agent behavior (prevent remediation, suggest fixes, control modes)
- **AND** instruction is separate from user-facing message field

### Requirement: Tool Arguments Base Class
The system SHALL provide ToolArguments base class in mcp_core with tool collection support.

#### Scenario: Base model inheritance
- **WHEN** a tool defines argument model
- **THEN** model inherits from ToolArguments
- **AND** model benefits from common validation (extra="ignore", validate_assignment=True)

#### Scenario: Schema markdown generation
- **WHEN** ToolArguments.to_schema_markdown() is called
- **THEN** returns markdown-formatted argument schema
- **AND** includes argument names, types, required/optional status, and descriptions
- **AND** handles Literal types correctly

#### Scenario: Tool description building
- **WHEN** ToolArguments.build_tool_description(func) is called
- **THEN** combines function docstring with generated schema markdown
- **AND** returns complete tool description for MCP registration

### Requirement: Tool Collection Pattern
The system SHALL provide tool collection mechanism in ToolArguments for automatic discovery.

#### Scenario: Tool declaration
- **WHEN** @ToolArguments.declare decorator is applied to function
- **THEN** function is added to collection without wrapping
- **AND** function is returned unchanged for normal execution

#### Scenario: Collection retrieval
- **WHEN** ToolArguments.get_declared_tools() is called
- **THEN** returns dictionary of all declared tools
- **AND** clears collection to prevent double registration
- **AND** operation is thread-safe with asyncio lock

#### Scenario: Double registration prevention
- **WHEN** get_declared_tools() is called multiple times
- **THEN** second call returns empty dictionary
- **AND** tools are not registered twice with FastMCP

#### Scenario: Thread safety
- **WHEN** multiple coroutines access collection
- **THEN** asyncio lock protects _declared dictionary
- **AND** no race conditions occur during declare or get operations

### Requirement: Tool Name Decoration
The system SHALL provide ExtMcpToolDecorator in mcp_core that adds configurable prefixes.

#### Scenario: No default prefix
- **WHEN** ExtMcpToolDecorator is initialized without prefix parameter
- **THEN** reads prefix from MCP_TOOL_PREFIX environment variable
- **AND** uses empty string if environment variable not set

#### Scenario: Per-tool prefix override
- **WHEN** tool is decorated with prefix parameter
- **THEN** specified prefix is used instead of default
- **AND** empty string disables prefix for that tool

#### Scenario: Tool name prefixing
- **WHEN** tool is registered with decorator
- **THEN** final tool name is prefix + tool_name (if prefix not empty)
- **AND** tool is registered with FastMCP using final name

### Requirement: Automatic Tool Logging
The system SHALL automatically log all tool invocations via ExtMcpToolDecorator.

#### Scenario: Tool invocation logging
- **WHEN** tool is called
- **THEN** TRACE level log entry created with "Tool called: {name}"
- **AND** log entry created before tool executes

#### Scenario: Tool success logging (async)
- **WHEN** async tool completes successfully
- **THEN** TRACE level log entry created with "Tool {name} completed successfully"

#### Scenario: Tool success logging (sync)
- **WHEN** sync tool completes successfully
- **THEN** DEBUG level log entry created with "Tool {name} completed successfully"

#### Scenario: Tool failure logging
- **WHEN** tool raises exception
- **THEN** ERROR level log entry created with "Tool {name} failed: {error}"
- **AND** exception is re-raised after logging

### Requirement: Environment Configuration
The system SHALL configure MCP_TOOL_PREFIX early in mcp_guide startup.

#### Scenario: Default prefix configuration
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX not set
- **THEN** default tool prefix is empty string (no prefix)
- **AND** tools are registered without any prefix

#### Scenario: User-provided prefix preserved
- **WHEN** mcp_guide starts and MCP_TOOL_PREFIX is set to a non-empty value
- **THEN** existing value is used as the tool prefix
- **AND** tools are registered with that prefix

### Requirement: Tool Integration Pattern
The system SHALL integrate tool collection with FastMCP registration in server.py.

#### Scenario: Tool module import triggers collection
- **WHEN** tool modules are imported
- **THEN** @ToolArguments.declare decorators execute
- **AND** tools are added to collection

#### Scenario: Automatic registration with descriptions
- **WHEN** get_declared_tools() is called in server.py
- **THEN** for each tool, build_tool_description() generates complete description
- **AND** tool is registered with ExtMcpToolDecorator using generated description
- **AND** tool is registered with FastMCP

#### Scenario: Conditional example tool
- **WHEN** MCP_INCLUDE_EXAMPLE_TOOLS environment variable is "true"
- **THEN** tool_example module is imported
- **AND** example tools are included in registration
- **WHEN** environment variable is not "true"
- **THEN** tool_example module is not imported
- **AND** example tools are excluded

### Requirement: Explicit Use Pattern
The system SHALL support explicit user consent for destructive operations.

#### Scenario: Literal type enforcement
- **WHEN** destructive tool requires explicit consent
- **THEN** tool argument includes Literal type field
- **AND** field requires exact string match (e.g., "CREATE_DOCUMENT")
- **AND** Pydantic validation enforces literal value

#### Scenario: Tool description warning
- **WHEN** tool requires explicit consent
- **THEN** tool description includes "REQUIRES EXPLICIT USER INSTRUCTION"
- **AND** description explains consent requirement
- **AND** description warns against frivolous use

### Requirement: Tool Documentation Convention
The system SHALL enforce documentation conventions for tools.

#### Scenario: Undecorated name in documentation
- **WHEN** tool documentation is written
- **THEN** undecorated tool name is used
- **AND** prefix is not mentioned in documentation
- **AND** prefix is treated as implementation detail
- **AND** flag tools use explicit scope naming (project_flag vs feature_flag)

### Requirement: Project Flag Tool Naming
The system SHALL provide explicitly named tools for project flag operations.

#### Scenario: Project flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_project_flag` tool is registered for setting project flags
- **AND** `get_project_flag` tool is registered for getting project flags with resolution
- **AND** `list_project_flags` tool is registered for listing project flags

#### Scenario: Project flag resolution hierarchy
- **WHEN** `get_project_flag` or `list_project_flags` is called
- **THEN** project flags override global flags in resolution
- **AND** global flags provide defaults when project flags not set
- **AND** resolution hierarchy is preserved from original implementation

### Requirement: Global Flag Tool Naming
The system SHALL provide explicitly named tools for global flag operations.

#### Scenario: Global flag tool registration
- **WHEN** MCP server initializes
- **THEN** `set_feature_flag` tool is registered for setting global flags
- **AND** `get_feature_flag` tool is registered for getting global flags only
- **AND** `list_feature_flags` tool is registered for listing global flags only

#### Scenario: Global flag isolation
- **WHEN** global flag tools are called
- **THEN** operations work exclusively with `session.feature_flags()`
- **AND** no resolution hierarchy or project flag merging occurs
- **AND** operations are isolated to global scope only

### Requirement: Tool and Prompt Description Standards
The system SHALL enforce standardized 4-section documentation format for all MCP tools and prompts.

#### Scenario: Tool documentation format
- **WHEN** tool documentation is written
- **THEN** docstring includes Description section (≤50 chars first line if possible)
- **AND** docstring includes JSON Schema section with Pydantic-generated schema
- **AND** docstring includes Usage Instructions section with code examples
- **AND** docstring includes Concrete Examples section with real scenarios

#### Scenario: Prompt documentation format
- **WHEN** prompt documentation is written
- **THEN** docstring includes Description section (≤50 chars first line if possible)
- **AND** docstring includes Conceptual Schema section using *args interface
- **AND** docstring includes Usage Instructions section with @prompt_name syntax
- **AND** docstring includes Concrete Examples section with real invocations

#### Scenario: Field description completeness
- **WHEN** tool argument models are defined
- **THEN** all Pydantic fields include Field(description=...) parameters
- **AND** descriptions are clear, concise, and consistent with established patterns
- **AND** schema generation includes all field descriptions

#### Scenario: Documentation template references
- **WHEN** tool or prompt modules are created
- **THEN** module includes reference comment to appropriate README template
- **AND** tools reference src/mcp_guide/tools/README.md
- **AND** prompts reference src/mcp_guide/prompts/README.md

#### Scenario: Prompt varargs documentation
- **WHEN** prompt uses arg1...argF implementation pattern
- **THEN** documentation shows conceptual *args interface
- **AND** implementation details (arg1, arg2, etc.) are hidden from users
- **AND** examples use clean @prompt_name syntax

### Requirement: Direct Tool Invocation
The system SHALL allow prompts to call existing tools directly without decorator overhead.

#### Scenario: Tool function extraction
- **WHEN** prompt needs to call existing tool logic
- **THEN** tool implementation is accessible without decorator
- **AND** maintains same argument and context patterns

### Requirement: Client Info Utility Tool
The system SHALL provide a `client_info` utility tool that returns information
about the agent/client environment.

Arguments:
- `verbose` (optional, boolean): include detailed information when available.

The tool SHALL return a Result pattern response containing available agent name,
version, and client environment details.

#### Scenario: Retrieve client information
- **WHEN** `client_info` is invoked
- **THEN** it SHALL return available agent name, version, and environment details
- **AND** the response SHALL use the standard Result pattern

### Requirement: Tool Description Standard for AI Agents
The system SHALL provide a standardized format for tool descriptions that enables AI agents to correctly understand and invoke tools without trial-and-error.

#### Scenario: Concise description structure
- **WHEN** a tool is documented
- **THEN** the docstring on the registered tool function contains a concise description (2-4 sentences)
- **AND** the description covers what the tool does and when to use it
- **AND** hand-written JSON Schema sections are NOT included in the docstring (redundant with auto-generated Arguments)
- **AND** Usage Instructions and Concrete Examples sections are NOT included (verbose, not MCP best practice)

#### Scenario: Auto-generated arguments section
- **WHEN** a tool is registered via `@toolfunc`
- **THEN** `build_description` appends a `## Arguments` block generated from Pydantic field descriptions
- **AND** this is the single source of parameter documentation for agents
- **AND** the combined description (concise docstring + auto-generated Arguments) is registered with FastMCP

#### Scenario: Template availability
- **WHEN** developer creates new tool
- **THEN** `src/mcp_guide/tools/README.md` provides the concise description standard
- **AND** template shows correct docstring placement on the registered function (not `internal_*`)
- **AND** template includes example of Pydantic Field descriptions that generate the Arguments section

#### Scenario: Docstring placement
- **WHEN** a tool has an `internal_*` implementation function
- **THEN** the agent-facing docstring is on the registered `@toolfunc` function
- **AND** the `internal_*` function may have a minimal or no docstring

#### Scenario: Complete field descriptions
- **WHEN** tool argument model is defined with Pydantic
- **THEN** every field includes `Field(description="...")` parameter
- **AND** description explains field purpose and valid values
- **AND** generated `## Arguments` block includes all field descriptions

### Requirement: Slash Syntax Content Retrieval
The system SHALL support `category/pattern` syntax as shorthand for two-parameter content retrieval.

#### Scenario: Basic slash syntax
- **WHEN** `get_content("lang/python")` is called
- **THEN** it SHALL be equivalent to `get_content("lang", "python")`
- **AND** the category is "lang" and pattern is "python"

### Requirement: Multi-Pattern Category Support
The system SHALL support multiple patterns within a single category using `+` separator.

#### Scenario: Multiple patterns with plus separator
- **WHEN** `get_content("lang/python+java+rust")` is called
- **THEN** content matching ANY of the patterns SHALL be retrieved
- **AND** results from all matching patterns SHALL be aggregated

### Requirement: Multi-Category Expression Support
The system SHALL support comma-separated expressions for retrieving content from multiple categories.

#### Scenario: Multi-category comma separation
- **WHEN** `get_content("lang/python,docs/api,guidelines")` is called
- **THEN** content SHALL be retrieved from all three specifications
- **AND** results SHALL be aggregated in order

### Requirement: CategoryCollection Args Cross-Field Validation
`CategoryCollectionAddArgs`, `CategoryCollectionChangeArgs`, and `CategoryCollectionUpdateArgs` SHALL reject incompatible field combinations at model construction time with a descriptive `ValueError`.

Fields that are category-only (`dir`, `patterns`, `new_dir`, `new_patterns`, `add_patterns`, `remove_patterns`) MUST NOT be provided when `type='collection'`.

Fields that are collection-only (`categories`, `new_categories`, `add_categories`, `remove_categories`) MUST NOT be provided when `type='category'`.

#### Scenario: Category-only fields rejected for collection type
- **WHEN** `CategoryCollectionAddArgs(type='collection', name='all', dir='docs/')` is constructed
- **THEN** a `ValueError` is raised indicating `dir` is not valid for `type='collection'`

#### Scenario: Collection-only fields rejected for category type
- **WHEN** `CategoryCollectionAddArgs(type='category', name='docs', categories=['guidelines', 'specs'])` is constructed
- **THEN** a `ValueError` is raised indicating `categories` is not valid for `type='category'`

#### Scenario: Compatible fields accepted
- **WHEN** `CategoryCollectionAddArgs(type='category', name='docs', dir='docs/')` is constructed
- **THEN** no error is raised

### Requirement: Update Documents Tool
The system SHALL provide an MCP tool `update_documents` that updates
documentation files in docroot using the same smart update logic as
`mcp-install update`.

#### Scenario: Tool accepts no arguments
- **WHEN** tool is registered
- **THEN** it accepts no parameters
- **AND** uses session docroot automatically

#### Scenario: Tool works without bound project
- **WHEN** tool is invoked in a session with no bound project
- **AND** global configuration can resolve docroot
- **THEN** the update proceeds using that docroot
- **AND** no `no_project` error is returned

#### Scenario: Tool fails when docroot cannot be resolved
- **WHEN** tool is invoked
- **AND** configuration cannot be read or docroot cannot be resolved
- **THEN** a configuration-related error is returned
- **AND** the tool does not require a bound project as part of that failure path

#### Scenario: No update needed
- **WHEN** tool is invoked
- **AND** `.version` file exists in docroot
- **AND** version matches current package version
- **THEN** success result is returned
- **AND** response indicates that no update was applied

### Requirement: Modern Tool Result Adaptation
The system SHALL convert internal tool `Result` values into SDK-native MCP tool
responses through one protocol adapter. The adapter SHALL preserve result content,
error status, `instruction`, and `additional_agent_instructions` semantics while
placing protocol metadata in the modern response structure.

#### Scenario: Successful tool result
- **WHEN** a tool returns a successful internal result
- **THEN** the protocol adapter SHALL emit a modern tool response with equivalent content and instruction semantics
- **AND** it SHALL not require the tool implementation to serialize a JSON result string for the SDK

#### Scenario: Failed tool result
- **WHEN** a tool returns a failed internal result
- **THEN** the protocol adapter SHALL emit the corresponding modern error/content response
- **AND** the client-visible error and embedded instructions SHALL be retained

### Requirement: Request-Scoped Tool Invocation
The tool registration layer SHALL normalise each invocation through the request adapter
and SHALL not use a global active session. It may continue to pass raw FastMCP context
to transitional tool implementations; replacing those handler signatures with resolved
application RequestContext is deferred to `use-request-context`.

The shared tool-argument contract SHALL include an optional FastMCP `session_id`.
The registration layer SHALL pass it to the request adapter when supplied, rather
than requiring individual tool implementations to resolve session ownership.

#### Scenario: A bound tool returns a new session ID
- **WHEN** `set_project(path)` or a stdio-PWD bootstrap creates and binds a FastMCP
  session
- **THEN** the common Result adapter SHALL include that `session_id` in the result's
  standard structured fixture
- **AND** it SHALL omit the fixture from results that neither create nor need to
  communicate a session ID

#### Scenario: Project-bound tool invocation
- **WHEN** a project-bound tool receives a request without valid project context
- **THEN** the registration layer SHALL return the no-project result before invoking the tool implementation
- **AND** it SHALL not create or persist a project from server process state, except
  for the optional inherited-`PWD` bootstrap of an unbound stdio interaction when
  that bootstrap has been explicitly enabled

### Requirement: Path-Based Project Selection
The public `set_project` tool SHALL accept required `path`, an absolute client
filesystem project-root path, rather than a project `name`. It SHALL derive the root
identity from that path and bind only an unbound interaction. `switch_project(name)`
remains the independent active Guide configuration-project operation and SHALL not
change root binding. It SHALL resolve named configuration selection with the bound
root's hash, preserving same-named configurations at different roots.

#### Scenario: Agent selects its root
- **WHEN** an agent calls `set_project` with an absolute `path`
- **THEN** the tool SHALL bind the unbound interaction to the project identified by that path
- **AND** the agent-visible tool schema SHALL not offer a name-only selection argument

#### Scenario: Bound interaction calls set_project
- **WHEN** an interaction already has a bound root and calls `set_project` with any path
- **THEN** the tool SHALL reject the call without changing the root or active configuration selection

#### Scenario: Configuration switch uses the bound root identity
- **WHEN** a root-bound interaction calls `switch_project` with a configuration `name`
- **THEN** it SHALL resolve or create that configuration using the bound root hash
- **AND** it SHALL reject a filesystem path passed to `switch_project`
- **AND** it SHALL NOT select a same-named configuration with a missing or different hash

### Requirement: Current-Target Configuration Cloning
The public `clone_project` tool SHALL accept only source configuration
`from_project`, merge, and force arguments. `from_project` SHALL accept either a
display name or an exact hash-suffixed configuration key. The tool SHALL clone into
the active configuration project of the root-bound interaction and SHALL NOT accept
`to_project`, a target key, or a target path. The target write SHALL use the active
configuration's exact key and bound root hash.

An exact hash-suffixed source key SHALL be used directly and SHALL NOT fall back to
display-name resolution. For a source name without a hash suffix, lookup SHALL use the
first strict configuration whose `Project.name` matches in configuration order. If no
strict match exists, cloning SHALL recover an exact raw hashless YAML key with the
requested name as its source. Ordinary configuration loading, selection, and listing
continue to ignore hashless, malformed, and mismatched entries.

#### Scenario: Clone into current configuration
- **WHEN** a root-bound interaction calls `clone_project` with an exact source key or a source configuration name
- **THEN** the tool SHALL copy configuration into that interaction's active configuration
- **AND** it SHALL NOT create, select, or modify any separately named target configuration

#### Scenario: Clone target is supplied
- **WHEN** a caller supplies a removed target-project argument to `clone_project`
- **THEN** the tool schema SHALL reject the request
- **AND** it SHALL not modify configuration

#### Scenario: Exact hash-suffixed source key
- **WHEN** `from_project` exactly matches a stored hash-suffixed configuration key
- **THEN** `clone_project` SHALL use that configuration as the source
- **AND** it SHALL not perform display-name ambiguity resolution

#### Scenario: Multiple source configurations with the same name
- **WHEN** more than one valid stored configuration has the requested source name
- **THEN** `clone_project` SHALL use the first matching configuration in configuration order

### Requirement: Tool Application Context Boundary
The tool registration layer SHALL adapt raw FastMCP invocation data into a resolved
RequestContext before invoking Guide tool application code. Internal tool
implementations and delegated tool helpers SHALL use that context rather than raw
FastMCP context.

#### Scenario: Tool delegates to another application helper
- **WHEN** a Guide tool delegates to content, project, category, collection, rendering,
  or task-result work
- **THEN** the delegated work SHALL receive the same resolved RequestContext
- **AND** it SHALL operate on the same Session and Project as the public tool invocation
