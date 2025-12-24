# User Documentation Updates Specification

## Overview

This specification defines the user-facing documentation that must be added to help users effectively use MCP Guide features.

## Documentation Requirements

### Pattern Syntax Documentation
**Location**: `docs/patterns.md` (new file)

**Content Requirements**:
- Glob pattern basics (*, **, ?, [])
- Recursive directory matching with **
- File extension patterns (*.md, *.{py,js})
- Directory-specific patterns (src/**/*.py)
- Exclusion patterns and limitations
- Practical examples for common use cases

### MIME-Multipart Format Documentation
**Location**: `docs/output-formats.md` (new file)

**Content Requirements**:
- When to use MIME format vs plain format
- How to enable MIME format in tools
- Output format structure and boundaries
- Use cases: multiple files, structured content
- Integration with external tools
- Examples of MIME output

### Template Syntax Documentation
**Location**: `docs/templates.md` (new file)

**Content Requirements**:
- Chevron template basics (variables, sections, partials)
- Link to official Chevron documentation
- Link to Mustache specification
- MCP Guide specific template features
- File detection (.mustache, .hbs extensions)
- Template rendering pipeline
- Error handling and debugging

### Template Context Reference
**Location**: `docs/template-context.md` (new file)

**Content Requirements**:
- **System Context**: timestamp, date formatting functions
- **Agent Context**: agent name, version, prompt prefix
- **Project Context**: project name, flags, configuration
- **Category Context**: category metadata, file information
- **File Context**: file path, metadata, template detection
- **Template Functions**: format_date, truncate, highlight_code
- **Context Hierarchy**: precedence and inheritance rules

## Documentation Standards

### Format Requirements
- Use Markdown format
- Include practical code examples
- Provide working sample configurations
- Link to external authoritative sources
- Use consistent heading structure

### Example Requirements
- Each feature must have at least 2 practical examples
- Examples should be copy-pasteable
- Include both simple and advanced use cases
- Show expected output where relevant

### Cross-References
- Link between related documentation sections
- Reference implementation files where appropriate
- Include troubleshooting sections
- Provide "See Also" sections

## Integration Requirements

### README Updates
- Add links to new documentation files
- Update feature overview with documentation references
- Ensure documentation is discoverable

### Existing Documentation
- Update any existing files that overlap with new content
- Ensure consistency across all documentation
- Remove or update outdated information

## Validation Requirements

### Content Accuracy
- All examples must be tested and working
- Code samples must match actual implementation
- Links must be valid and current

### User Experience
- Documentation must be accessible to new users
- Progressive complexity (basic → advanced)
- Clear navigation between topics
- Searchable content structure
