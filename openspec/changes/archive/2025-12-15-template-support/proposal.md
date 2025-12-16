# Change: Template Support

## Why

Template support is essential for dynamic content generation in mcp-guide. Currently, template discovery is implemented but template rendering and context resolution are missing. We need complete template support with:

- Mustache/Chevron template rendering for `.mustache` files
- Rich template context from project, category, collection, file, and agent data
- Proper error handling for template syntax errors
- Stateless context resolution (no caching complexity)
- Security considerations for dockerized MCP environments

Template functionality was originally part of `add-content-tools` but has been separated into its own feature for better modularity and focused implementation.

## What Changes

### Template Rendering Engine
- Integrate Chevron library for Mustache template rendering
- Detect `.mustache` files during content retrieval
- Render templates with dynamic context before returning content
- Pass through non-template files unchanged
- Handle template syntax errors gracefully with Result pattern

### Template Context Resolution
- **Project context**: name, categories list, collections list, created_at, updated_at
- **File context**: path, basename, category, collection, size (rendered), mtime, ctime (optional)
- **Category context**: name, dir (relative path), description
- **Collection context**: name, categories list, description (when applicable)
- **Agent context**: ALL available agent info + `@` variable for prompt character
- **System context**: now (ISO timestamp), timestamp (Unix)
- **Context priority**: File > Category > Collection > Project > Agent > System (later overrides earlier)

### Error Handling
- Template syntax errors return Result.failure with `template_error` type
- Missing variables render as empty strings (Chevron default, forgiving)
- Template errors logged at WARNING level for debugging
- Clear error messages with agent instructions
- No fallback to raw template content (fail fast)

### Security & Architecture
- No docroot path exposure (dockerized MCP consideration)
- Relative paths only in category context
- Stateless context computation (no caching complexity)
- Compatible with remote/containerized MCP servers

### Integration Points
- Template rendering occurs after file discovery and reading, before content formatting
- Integrates with existing content retrieval tools (get_category_content, get_collection_content, get_content)
- FileInfo enhanced with optional ctime field and rendered size tracking
- Works with both single file and MIME multipart responses

## Impact

- Affected specs: New capability `template-support`
- Affected code: New template rendering module, context resolution, FileInfo enhancements
- Dependencies: Chevron library (already added), Result pattern (ADR-003), existing content tools
- Breaking changes: None (enhancement to existing functionality)
- Performance: Stateless approach, no caching (simple and reliable)
- Security: No filesystem exposure, relative paths only
- Future expansion: Template validation/check mode for development debugging
