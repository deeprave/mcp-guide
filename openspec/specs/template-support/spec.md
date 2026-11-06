# template-support Specification

## Purpose
Define shared template context, caching, and helper support for document rendering.
## Requirements
### Requirement: Template Context Cache System (IMPLEMENTED ✅ - Phase 4)

The system SHALL provide a session-aware template context caching system that integrates with MCP session management.

Template context caching SHALL implement SessionListener for invalidation,
provide lazily loaded cached context data, and support system, agent, and
project context layers with defined precedence.

#### Scenario: Template context cache initialization
- **WHEN** TemplateContextCache is created
- **THEN** initialize as SessionListener with empty cache state

#### Scenario: Context cache invalidation on session change
- **WHEN** session changes for a project
- **THEN** invalidate cached template contexts to ensure fresh data

### Requirement: Template context cache session safety

Template context caching SHALL handle missing sessions and projects gracefully
and use safe attribute access without coupling to Session internals.

#### Scenario: Safe session access
- **WHEN** accessing session project data
- **THEN** use getattr() for safe access without direct private attribute coupling

### Requirement: Enhanced Session API (IMPLEMENTED ✅ - Phase 4)

The system SHALL provide an enhanced session API for template context integration.

Session API enhancements SHALL include:
- get_current_session() with optional project_name parameter
- Backward compatibility with existing get_current_session(project_name) usage
- Return first available session when no project_name specified

#### Scenario: Session access without project name
- **WHEN** calling get_current_session() without arguments
- **THEN** return first available session from active sessions

#### Scenario: Session access with project name
- **WHEN** calling get_current_session(project_name)
- **THEN** return specific session for that project (existing behavior)

### Requirement: Template Lambda Functions (IMPLEMENTED ✅)

The system SHALL provide advanced template functionality through lambda
functions that support complex data formatting and processing.

Template lambda functions SHALL:
- Follow Chevron's declared extension protocols
- Integrate with ChainMap context system for data access
- Support class-based architecture for clean dependency management
- Handle parsing errors gracefully with clear error messages

#### Lambda Function: format_date
The system SHALL provide date formatting capabilities through `format_date` lambda function.

Date formatting SHALL:
- Accept strftime format patterns as template text
- Parse variable references from template content
- Format datetime objects using Python strftime
- Support all standard strftime format codes

**Usage Pattern**: `{{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}`

#### Scenario: Date formatting with strftime
- **WHEN** template contains `{{#format_date}}%B %d, %Y{{created_at}}{{/format_date}}`
- **AND** context contains `created_at` with datetime(2023, 12, 25)
- **THEN** render as "December 25, 2023"

#### Lambda Function: truncate
The system SHALL provide text truncation capabilities through `truncate` lambda function.

Text truncation SHALL:
- Accept maximum length as numeric parameter
- Parse variable references from template content
- Truncate text to specified length with ellipses
- Handle edge cases (empty text, negative lengths)

**Usage Pattern**: `{{#truncate}}50{{description}}{{/truncate}}`

#### Scenario: Text truncation with ellipses
- **WHEN** template contains `{{#truncate}}20{{description}}{{/truncate}}`
- **AND** context contains long description text
- **THEN** truncate to 20 characters and append "..."

#### Lambda Function: highlight_code
The system SHALL provide language-labelled Markdown code fencing through the
`highlight_code` lambda function.

Code fencing SHALL:
- Accept programming language as parameter
- Parse code content from variable references
- Generate markdown code blocks with language specification

**Usage Pattern**: `{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}`

#### Scenario: Code fencing with markdown
- **WHEN** template contains `{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}`
- **AND** context contains Python code in `code_snippet`
- **THEN** render as markdown code block with python language tag

### Requirement: Template Detection and Rendering

The system SHALL provide mustache template rendering for files with `.mustache` extension.

Template rendering SHALL:
- Detect files with `.mustache` extension during content retrieval
- Render templates using Chevron library with mustache syntax
- Pass through non-template files unchanged
- Return rendered content in tool responses
- Handle template syntax errors gracefully using Result pattern

#### Scenario: Mustache file detected
- **WHEN** file has `.mustache` extension
- **THEN** render as mustache template with context before returning content

#### Scenario: Non-template file
- **WHEN** file does not have `.mustache` extension
- **THEN** return file content unchanged

#### Scenario: Template syntax error
- **WHEN** template has invalid mustache syntax
- **THEN** return Result.failure with error_type "template_error" and clear error message

#### Scenario: Template rendering in single response
- **WHEN** single template file matches pattern
- **THEN** render template and return as plain markdown

#### Scenario: Template rendering in MIME multipart
- **WHEN** multiple files include templates
- **THEN** render each template before adding to multipart response

### Requirement: Template Context Resolution with TemplateContext

The system SHALL provide rich context data for template rendering using a type-safe ChainMap-based context system.

TemplateContext SHALL extend ChainMap for scope chaining, priority resolution,
and hard or soft deletion.

#### Scenario: TemplateContext scope chaining
- **WHEN** file context contains same key as category context
- **THEN** file context value overrides category context value

#### Scenario: TemplateContext hard deletion
- **WHEN** deleting key from child context using del or hard_delete()
- **THEN** parent context value becomes visible for that key

#### Scenario: TemplateContext soft deletion
- **WHEN** soft-deleting key from child context
- **THEN** key appears missing (KeyError) even if present in parent

### Requirement: Template context source precedence

Context sources SHALL apply in this order, with later sources overriding earlier:
system context, agent context, and project context.

#### Scenario: Project source overrides system source
- **WHEN** a context value exists in system and project sources
- **THEN** the project source value takes precedence

### Requirement: Template context local source precedence

Collection, category, file, and template-lambda sources SHALL apply after
system, agent, and project sources, in that order.

#### Scenario: Context priority resolution
- **WHEN** variable defined in multiple context sources
- **THEN** use value from highest priority source (file overrides category, etc.)

### Requirement: Fresh template context construction

Context resolution SHALL use TemplateContext.new_child(), compute fresh context
for every render, convert datetime values to ISO 8601 and Path values to
strings, handle missing optional values, validate data at creation, and inject
TemplateFunctions.

#### Scenario: Context variable access
- **WHEN** template uses `{{project.name}}`
- **THEN** substitute with current project name from context

#### Scenario: Missing context variable
- **WHEN** template references undefined variable
- **THEN** render as empty string (Chevron default behavior)

#### Scenario: Context priority resolution
- **WHEN** variable defined in multiple context sources
- **THEN** use value from highest priority source (file overrides category, etc.)

#### Scenario: Agent prompt character access
- **WHEN** template uses `{{@}}`
- **THEN** substitute with agent's prompt character (e.g., "guide", "/")

#### Scenario: Lambda function integration
- **WHEN** template uses lambda functions with context variables
- **THEN** lambda functions access full context hierarchy through ChainMap

### Requirement: TemplateContext Type Safety

The system SHALL enforce type safety for template context data.

TemplateContext SHALL accept only string keys and str, dict, list, int, float,
bool, or None values. Nested dictionaries and list items SHALL also be valid
template values; internal soft-deletion sentinels remain supported.

#### Scenario: Valid context types
- **WHEN** setting context with str, int, float, bool, None, dict, or list values
- **THEN** accept the values without error

### Requirement: TemplateContext validation lifecycle

Type validation SHALL occur at context creation and modification, raise
descriptive TypeError exceptions for invalid values, and prevent invalid data
from reaching rendering.

#### Scenario: Invalid key type
- **WHEN** attempting to set non-string key in context
- **THEN** raise TypeError indicating keys must be strings

#### Scenario: Invalid value type
- **WHEN** attempting to set invalid value type (e.g., object, function)
- **THEN** raise TypeError indicating valid template value types

#### Scenario: Nested validation
- **WHEN** setting nested dict with invalid key or value types
- **THEN** raise TypeError during validation of nested structure

### Requirement: Project Context Variables

The system SHALL provide project-level context variables.

Project context SHALL include:
- `name`: Project name (string)
- `created_at`: Project creation timestamp (ISO 8601 string)
- `updated_at`: Project last update timestamp (ISO 8601 string)
- `categories`: List of category names (array of strings)
- `collections`: List of collection names (array of strings)

#### Scenario: Project name access
- **WHEN** template uses `{{project.name}}`
- **THEN** substitute with current project name

#### Scenario: Project categories list
- **WHEN** template uses `{{#project.categories}}{{.}}{{/project.categories}}`
- **THEN** iterate over all category names in project

#### Scenario: Project collections list
- **WHEN** template uses `{{#project.collections}}{{.}}{{/project.collections}}`
- **THEN** iterate over all collection names in project

### Requirement: File Context Variables

The system SHALL provide file-level context variables for the current file being rendered.

File context SHALL include relative `path`, extension-free `basename`, and
optional `category` and `collection` names.

#### Scenario: File path access
- **WHEN** template uses `{{file.path}}`
- **THEN** substitute with relative path from category directory

#### Scenario: File basename access
- **WHEN** template uses `{{file.basename}}`
- **THEN** substitute with filename without .mustache extension

### Requirement: File context metadata values

File context SHALL include integer `size`, ISO 8601 `mtime`, and optional ISO
8601 `ctime`; template size SHALL represent rendered content size.

#### Scenario: File size for templates
- **WHEN** rendering template file
- **THEN** file.size reflects rendered content size, not original template size

#### Scenario: File creation time handling
- **WHEN** ctime is unavailable on platform
- **THEN** file.ctime is None and renders as empty string

### Requirement: Category Context Variables

The system SHALL provide category-level context variables.

Category context SHALL include:
- `name`: Category name (string)
- `dir`: Category directory path relative to docroot (string)
- `description`: Category description (string or None)

Security constraint: Category dir SHALL be relative path only, never absolute path.

#### Scenario: Category name access
- **WHEN** template uses `{{category.name}}`
- **THEN** substitute with category name

#### Scenario: Category relative directory
- **WHEN** template uses `{{category.dir}}`
- **THEN** substitute with relative directory path (e.g., "docs", "guides/advanced")

#### Scenario: Category description handling
- **WHEN** category has no description
- **THEN** category.description is None and renders as empty string

#### Scenario: Docroot security
- **WHEN** building category context
- **THEN** never expose absolute docroot path for security (dockerized MCP)

### Requirement: Collection Context Variables

The system SHALL provide collection-level context variables when file is accessed via collection.

Collection context SHALL include:
- `name`: Collection name (string)
- `categories`: List of category names in collection (array of strings)
- `description`: Collection description (string or None)

Collection context SHALL be None when file is accessed directly via category.

#### Scenario: Collection name access
- **WHEN** template uses `{{collection.name}}` and file accessed via collection
- **THEN** substitute with collection name

#### Scenario: Collection categories list
- **WHEN** template uses `{{#collection.categories}}{{.}}{{/collection.categories}}`
- **THEN** iterate over category names in the collection

#### Scenario: No collection context
- **WHEN** file accessed directly via category (not through collection)
- **THEN** collection context is None and collection variables render as empty

### Requirement: Template Context Variables
The system SHALL provide a `tool_prefix` variable in the agent template context for dynamic MCP tool references.

#### Scenario: Tool prefix available in templates
- **WHEN** a template is rendered
- **THEN** `{{tool_prefix}}` is available in the template context

### Requirement: Dynamic Tool References
Templates SHALL support dynamic tool name construction using the tool_prefix variable.

#### Scenario: Portable tool references
- **GIVEN** a template references `{{tool_prefix}}tool_name`
- **WHEN** rendered with different MCP_TOOL_PREFIX values
- **THEN** the tool reference SHALL adapt to the configured prefix
- **AND** maintain correct underscore separation

### Requirement: System Context Variables

The system SHALL provide system-level built-in context variables.

System context SHALL include:
- `timestamp`: Current Unix timestamp (float with decimal precision)
- `timestamp_ms`: Current timestamp in milliseconds (float)
- `timestamp_ns`: Current timestamp in nanoseconds (integer)
- `now`: Structured local datetime with fields: date, day, time, tz, datetime
- `now_utc`: Structured UTC datetime with fields: date, day, time, tz, datetime

#### Scenario: Current datetime field access
- **WHEN** template uses `{{now.date}}`
- **THEN** substitute with formatted local date (e.g., "2025-12-14")

#### Scenario: UTC datetime field access
- **WHEN** template uses `{{now_utc.time}}`
- **THEN** substitute with UTC time in HH:MM format

#### Scenario: Unix timestamp access
- **WHEN** template uses `{{timestamp}}`
- **THEN** substitute with current Unix timestamp as float with decimal precision

#### Scenario: High precision timestamps
- **WHEN** template uses `{{timestamp_ms}}` or `{{timestamp_ns}}`
- **THEN** substitute with millisecond or nanosecond precision timestamps

#### Scenario: Timestamp consistency
- **WHEN** multiple timestamp variables used in same template
- **THEN** all timestamps reflect same moment in time (context computed once per render)

#### Scenario: Structured datetime access
- **WHEN** template uses `{{now.day}}` or `{{now_utc.tz}}`
- **THEN** access individual datetime components as strings

### Requirement: Template Error Handling

The system SHALL handle template errors gracefully with proper error reporting.

Error handling SHALL:
- Catch Chevron parsing and rendering errors
- Return Result.failure with error_type "template_error"
- Log template errors at WARNING level
- Provide clear error messages with file path and error details
- Set disposition `agent/error` so the taught vocabulary conveys that the failure is fixable by the agent, without a paired prose restatement
- Never fall back to raw template content

#### Scenario: Template parse error
- **WHEN** template has malformed mustache syntax
- **THEN** return Result.failure with specific parse error message

#### Scenario: Template render error
- **WHEN** template rendering fails during execution
- **THEN** return Result.failure with rendering error details

#### Scenario: Error logging
- **WHEN** template error occurs
- **THEN** log error at WARNING level with file path and error message

#### Scenario: Agent error instruction
- **WHEN** template error occurs
- **THEN** set disposition `agent/error` on the result
- **AND** do not additionally include a paired instruction restating what the disposition already conveys

#### Scenario: No fallback behavior
- **WHEN** template error occurs
- **THEN** do not return raw template content, always return error Result

### Requirement: FileInfo Enhancement

The system SHALL enhance FileInfo model to support template rendering metadata.

FileInfo enhancements SHALL include:
- `ctime`: Optional file creation time (datetime or None)
- `size`: File size that reflects rendered content size for templates
- Existing fields: path, basename, mtime, content, category, collection

Size handling SHALL:
- For non-template files: original file size
- For template files: rendered content size after template processing

#### Scenario: Creation time metadata
- **WHEN** file system supports creation time
- **THEN** populate FileInfo.ctime with creation timestamp

#### Scenario: Creation time unavailable
- **WHEN** file system does not support creation time
- **THEN** FileInfo.ctime is None

#### Scenario: Template size tracking
- **WHEN** template file is rendered
- **THEN** FileInfo.size reflects rendered content size, not original template size

#### Scenario: Non-template size tracking
- **WHEN** non-template file is processed
- **THEN** FileInfo.size reflects original file size

### Requirement: Integration with Content Tools

The system SHALL integrate template rendering with existing content retrieval tools.

Integration SHALL:
- Render templates during content retrieval pipeline
- Occur after file discovery and reading, before content formatting
- Work with get_category_content, get_collection_content, and get_content tools
- Support both single file and MIME multipart responses
- Maintain existing tool argument schemas and behavior

#### Scenario: Template rendering pipeline
- **WHEN** content tool retrieves files
- **THEN** execute: discover → read → render templates → format response

#### Scenario: Single template response
- **WHEN** content tool returns single template file
- **THEN** render template and return as plain markdown

#### Scenario: Mixed content response
- **WHEN** content tool returns mix of template and non-template files
- **THEN** render only template files, pass through others unchanged

#### Scenario: MIME multipart with templates
- **WHEN** multiple files include templates in MIME response
- **THEN** render templates before adding to multipart format

### Requirement: Template Error Signaling

The system SHALL provide an `_error` template lambda that allows templates to signal application-level errors through the rendering pipeline.

The `_error` lambda SHALL be registered in the common rendering pipeline for
all template types, render its enclosed block with the current context, and
return an empty string so error content is absent from output.

#### Scenario: Template signals missing argument error
- **WHEN** a command template renders `{{#_error}}Missing required argument{{/_error}}`
- **THEN** the rendered output SHALL NOT contain the error message
- **AND** the error message SHALL be captured by the rendering pipeline

### Requirement: Template error accumulation

The `_error` lambda SHALL append each rendered message to TemplateFunctions
and support multiple invocations in order.

#### Scenario: Multiple errors accumulated
- **WHEN** a template invokes `_error` multiple times
- **THEN** all error messages SHALL be collected in order
- **AND** `RenderedContent.errors` SHALL contain all messages

#### Scenario: Errors propagate through RenderedContent
- **WHEN** a template signals one or more errors via `_error` lambda
- **THEN** `RenderedContent.errors` SHALL contain the error messages
- **AND** callers SHALL handle errors appropriately for their context

#### Scenario: No error signaled
- **WHEN** a template renders without invoking `_error`
- **THEN** `RenderedContent.errors` SHALL be an empty list
- **AND** the result SHALL proceed as normal

#### Scenario: Error with rendered context variables
- **WHEN** a template renders `{{#_error}}Missing: {{variable_name}}{{/_error}}`
- **THEN** the error message SHALL contain the rendered value of `variable_name`

#### Scenario: Available across all template types
- **WHEN** any template type (command, openspec, workflow, context) is rendered through the common pipeline
- **THEN** the `_error` lambda SHALL be available for use
- **AND** errors SHALL propagate via `RenderedContent.errors` to the respective caller

#### Scenario: Errors from partials propagate to parent
- **WHEN** a partial template invokes `{{#_error}}...{{/_error}}`
- **THEN** the error SHALL accumulate in the same `RenderedContent.errors` as the parent template

### Requirement: Template Name Context Variable
The system SHALL inject `template_name` into the template context during rendering.

`template_name` SHALL be the stem of the template file path with any leading underscore stripped.

#### Scenario: template_name available in error messages
- **WHEN** a template renders `{{#_error}}Error in {{template_name}}: missing argument{{/_error}}`
- **THEN** the error message SHALL contain the resolved template name

### Requirement: Command Template Error Handling
When `_execute_command` renders a command template that signals errors via `_error`, it SHALL return a failure result.

The failure result SHALL:
- Set `error` to the newline-joined error messages
- Set `error_type` to `"validation"`
- Set `error_data` to `{"errors": [list of individual error messages]}`

#### Scenario: Command template signals validation error
- **WHEN** a command template invokes `{{#_error}}Missing required argument: name{{/_error}}`
- **THEN** `_execute_command` SHALL return `Result.failure` with `error_type="validation"`
- **AND** `error_data["errors"]` SHALL contain the error message
- **AND** the tool response SHALL have `success: false`
### Requirement: Content Accessor Lambda

The system SHALL provide a `resource` template lambda that renders content references in a configurable format.

The resource lambda SHALL accept an expression and be registered in template
context as `resource`.

#### Scenario: Default rendering (guide:// URI)
- **WHEN** `{{#resource}}guidelines{{/resource}}` is rendered
- **AND** `format-resource` is `false` or unset
- **THEN** output is `guide://guidelines`

### Requirement: Configurable resource-lambda rendering

The resource lambda SHALL use `format-resource`, exposed by `FLAG_RESOURCE` and
its registered boolean validator/normaliser. It SHALL render `guide://expression`
when false or unset and `get_content("expression")` when true; URI is default.

#### Scenario: Tool rendering
- **WHEN** `{{#resource}}guidelines{{/resource}}` is rendered
- **AND** `format-resource` is `true`
- **THEN** output is `get_content("guidelines")`

### Requirement: Guide URI Instruction Delivery

The system SHALL automatically inform agents about the guide:// URI scheme via a one-shot instruction.

Guide SHALL render `_system/guide-uri.mustache` on project load and queue it as
a non-priority, unacknowledged `agent/information` instruction. The instruction
SHALL be always active and not user-visible.

#### Scenario: Instruction delivery on project load
- WHEN a project is loaded for the first time in a session
- THEN the guide URI instruction is queued for delivery on next tool response

### Requirement: Guide URI instruction content

Guide URI instruction delivery SHALL reference MCP `resources/list` discovery
and explain that `read_resource` resolves guide:// URIs.


#### Scenario: Instruction is one-shot
- WHEN the guide URI instruction has been queued
- THEN it is not retried or re-queued on subsequent tool calls### Requirement: Command Accessor Lambda

The system SHALL provide a template helper family for rendering command references
in a configurable format.

The command helper family SHALL:
- Be registered in template context as `command`, `command-args`, `command-flags`,
  and `command-alias`
- Support composing a command reference from a base command plus adjacent
  arguments, flags, and aliases in the same template region
- Support a `format-command` feature flag, exposed by `FLAG_COMMAND`, that controls output format
- Render as a `guide://_...` command URI when `format-command` is `false` or unset
- Render as a tool-oriented command reference when `format-command` is `true`
- Use URI rendering as the universal default when `format-command` is unset

URI rendering SHALL follow the command-resource shape:
- base form: `guide://_{command}`
- positional args appended as path segments
- flags rendered as query parameters

Tool-oriented rendering SHALL follow the guide tool/reference shape:
- base form uses the effective prompt name and current prompt prefix when prompt-style output is required
- positional args rendered space-separated after the command
- flags rendered as `--name=value` or `--name` for truthy valueless flags

#### Scenario: URI rendering for explicit flag
- **WHEN** `{{#command}}doit{{/command}}{{#command-args}}now{{/command-args}}{{#command-flags}}verbose=true,from=hello{{/command-flags}}` is rendered
- **AND** `format-command` is `false` or unset
- **THEN** the output is a `guide://_doit/...` URI
- **AND** positional args are encoded as URI path segments
- **AND** flags are encoded as URI query parameters

#### Scenario: Tool-oriented rendering for explicit flag
- **WHEN** `{{#command}}doit{{/command}}{{#command-args}}now{{/command-args}}{{#command-flags}}verbose=true,from=hello{{/command-flags}}` is rendered
- **AND** `format-command` is `true`
- **THEN** the output is a tool-oriented command reference
- **AND** positional args are rendered after the command name
- **AND** flags are rendered with `--` syntax

#### Scenario: Unset command format chooses URI form
- **WHEN** `format-command` is unset
- **THEN** `{{#command}}status{{/command}}` renders as a `guide://_status` URI

#### Scenario: Adjacent helper sections compose one command reference
- **WHEN** `command`, `command-args`, `command-flags`, or `command-alias` helper sections are used adjacently in a template
- **THEN** they contribute to the same command reference rather than rendering independently

#### Scenario: Aliases can be rendered alongside command reference
- **WHEN** a template uses `{{#command}}help{{/command}}{{#command-alias}}?,h{{/command-alias}}`
- **THEN** the helper family provides access to the aliases for rendering
- **AND** alias formatting remains consistent with the selected `format-command` mode

#### Scenario: Shared helpers replace hardcoded template references
- **WHEN** an existing template renders guide command or resource references
- **AND** the shared `command` / `resource` helper family can express that reference
- **THEN** the template uses the shared helper family instead of hardcoded `@guide`, `/guide`, or ad hoc resource formatting

### Requirement: Prompt name override

The system SHALL allow the registered guide prompt name to be overridden by
environment variable.

The prompt naming behavior SHALL:
- Default to prompt name `guide` when no override is set
- Use `MCP_PROMPT_NAME` as the override source when present
- Apply the overridden name consistently to prompt registration and prompt-style
  command rendering
- Not affect `guide://` URI rendering, which remains on the `guide://` scheme

#### Scenario: Default prompt name remains guide
- **WHEN** `MCP_PROMPT_NAME` is unset
- **THEN** prompt registration uses `guide`

#### Scenario: Prompt name overridden by environment
- **WHEN** `MCP_PROMPT_NAME=g`
- **THEN** prompt registration uses `g`
- **AND** prompt-style command rendering uses `@g` or `/g` according to the client prefix

#### Scenario: URI rendering is unaffected by prompt override
- **WHEN** `MCP_PROMPT_NAME` is set
- **AND** a template renders `{{#command}}status{{/command}}` in URI mode
- **THEN** the output remains `guide://_status`

### Requirement: Prompt name variable

The template support system SHALL expose the effective prompt name as a simple
template variable for compatibility and edge-case templates.

#### Scenario: Prompt variable rendering
- **WHEN** a template renders `{{prompt}}`
- **THEN** the output is the effective prompt name
- **AND** if `MCP_PROMPT_NAME` is set, `{{prompt}}` reflects that override
- **AND** command helper templates remain the preferred mechanism for command references

### Requirement: Static documentation command format

Static documentation SHALL use `guide://` URI syntax as the canonical form for
guide command and resource references.

#### Scenario: Static docs prefer URI syntax
- **WHEN** static documentation includes guide command examples or resource references
- **THEN** the primary documented syntax is `guide://...`
- **AND** prompt-style syntax may appear only as a note or reminder, not as the canonical form
- **AND** static docs do not rely on a specific prompt prefix or fixed prompt name

### Requirement: Recommendation template helper
The common template context SHALL expose the `recommend` helper for every
template rendering surface. Rendering SHALL append each recommendation's
footnote directly to the rendered document before returning it. Result,
content, queue, listener, and response-adapter layers SHALL NOT carry
recommendation state.

#### Scenario: Helper is available in a skill template
- **WHEN** a Guide skill entrypoint uses the `recommend` helper
- **THEN** the entrypoint render includes the fluent reference and its footnote
- **AND** the rendered skill instructions do not include the helper marker

#### Scenario: Helper is available in an ordinary content template
- **WHEN** a command, workflow, context, or ordinary content template uses the
  `recommend` helper
- **THEN** its render includes the same typed recommendation footnote
