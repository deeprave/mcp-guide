# Specification: Template Support

## ADDED Requirements

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

Context resolution SHALL use a TemplateContext class that:
- Extends ChainMap for scope chaining behavior
- Validates context keys are strings and values are template-safe types
- Provides automatic priority resolution (inner scopes override outer scopes)
- Supports both hard deletion (reveals parent) and soft deletion (masks parent)
- Maintains type safety across all context operations

Context sources SHALL include (in priority order, later overrides earlier):
1. **System context**: Built-in variables (now, timestamp)
2. **Agent context**: Agent information and prompt character
3. **Project context**: Project configuration data
4. **Collection context**: Collection information (when applicable)
5. **Category context**: Category configuration data
6. **File context**: Current file metadata

Context resolution SHALL:
- Use TemplateContext.new_child() to create layered contexts
- Compute context fresh on every template render (stateless approach)
- Convert datetime objects to ISO 8601 strings
- Convert Path objects to strings for template compatibility
- Handle missing optional fields gracefully (None values)
- Validate all context data at creation time

#### Scenario: TemplateContext type validation
- **WHEN** creating context with invalid key type
- **THEN** raise TypeError with clear message about string keys requirement

#### Scenario: TemplateContext scope chaining
- **WHEN** file context contains same key as category context
- **THEN** file context value overrides category context value

#### Scenario: TemplateContext hard deletion
- **WHEN** deleting key from child context using del or hard_delete()
- **THEN** parent context value becomes visible for that key

#### Scenario: TemplateContext soft deletion
- **WHEN** soft-deleting key from child context
- **THEN** key appears missing (KeyError) even if present in parent

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

### Requirement: TemplateContext Type Safety

The system SHALL enforce type safety for template context data.

TemplateContext SHALL validate:
- Keys must be strings (for template variable names)
- Values must be str, dict, list, int, float, bool, or None
- Nested dictionaries have string keys and valid values
- List items are valid template values
- Special sentinel values for soft deletion are handled internally

Type validation SHALL:
- Occur at context creation and modification time
- Raise TypeError with descriptive messages for invalid types
- Allow internal sentinel values for soft deletion masking
- Prevent invalid data from reaching template rendering

#### Scenario: Valid context types
- **WHEN** setting context with str, int, float, bool, None, dict, or list values
- **THEN** accept the values without error

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

File context SHALL include:
- `path`: Relative path from category directory (string)
- `basename`: Filename without .mustache extension (string)
- `category`: Category name where file is located (string or None)
- `collection`: Collection name if applicable (string or None)
- `size`: File size in bytes, rendered content size for templates (integer)
- `mtime`: File modification time (ISO 8601 string)
- `ctime`: File creation time (ISO 8601 string or None if unavailable)

#### Scenario: File path access
- **WHEN** template uses `{{file.path}}`
- **THEN** substitute with relative path from category directory

#### Scenario: File basename access
- **WHEN** template uses `{{file.basename}}`
- **THEN** substitute with filename without .mustache extension

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

### Requirement: Agent Context Variables

The system SHALL provide agent-level context variables from MCP session.

Agent context SHALL include:
- `@`: Agent prompt character (string, short variable name)
- `agent.name`: Agent name (string or None)
- `agent.version`: Agent version (string or None)
- `agent.prompt_prefix`: Agent prompt prefix (string or None)
- All other available agent information fields

#### Scenario: Agent prompt character access
- **WHEN** template uses `{{@}}`
- **THEN** substitute with agent's prompt character (e.g., "guide", "/", "@")

#### Scenario: Agent name access
- **WHEN** template uses `{{agent.name}}`
- **THEN** substitute with agent name from session

#### Scenario: Missing agent info
- **WHEN** agent information not available in session
- **THEN** agent variables render as empty strings

#### Scenario: Agent prompt rendering
- **WHEN** template uses `{{@}}guide`
- **THEN** render as agent's prompt character + "guide" (e.g., "@guide", "/guide")

### Requirement: System Context Variables

The system SHALL provide system-level built-in context variables.

System context SHALL include:
- `now`: Current timestamp in ISO 8601 format (string)
- `timestamp`: Current Unix timestamp (integer)

#### Scenario: Current timestamp access
- **WHEN** template uses `{{now}}`
- **THEN** substitute with current timestamp in ISO 8601 format

#### Scenario: Unix timestamp access
- **WHEN** template uses `{{timestamp}}`
- **THEN** substitute with current Unix timestamp as integer

#### Scenario: Timestamp consistency
- **WHEN** multiple timestamp variables used in same template
- **THEN** all timestamps reflect same moment in time (context computed once per render)

### Requirement: Template Error Handling

The system SHALL handle template errors gracefully with proper error reporting.

Error handling SHALL:
- Catch Chevron parsing and rendering errors
- Return Result.failure with error_type "template_error"
- Log template errors at WARNING level
- Provide clear error messages with file path and error details
- Include agent instructions for error resolution
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
- **THEN** include instruction "Fix the template syntax or provide missing context variables"

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

## FUTURE Requirements (Not in Current Scope)

### Future Requirement: Template Validation Mode

**Note**: This requirement is documented for future planning but is NOT part of the current implementation scope.

The system MAY support template validation/check mode for development debugging.

Potential features:
- Strict mode that warns about missing variables
- Template syntax validation without rendering
- Context variable usage analysis
- Development-time template debugging tools
- Return warnings in Result for template development

**Recommendation**: Implement when template development workflow needs are identified.

### Future Requirement: Template Caching

**Note**: Caching was removed from current scope due to complexity with dynamic context data.

The system MAY support template caching in a future release if performance issues are identified.

Challenges:
- Dynamic context data (timestamps, agent info) changes frequently
- Cache invalidation complexity with context dependencies
- Memory management for cached templates and contexts

**Recommendation**: Profile performance and implement only if template rendering becomes a bottleneck.
