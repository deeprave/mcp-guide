# User Documentation Updates

**Priority**: Medium
**Complexity**: Low

## Why

The MCP Guide system has several user-facing features that lack proper documentation:

1. **Pattern Syntax**: Users need to understand how to configure category and collection patterns for file matching
2. **MIME Format**: The mime-multipart output format is available but undocumented - users don't know when/how to use it
3. **Template Syntax**: Chevron templating is supported but users lack guidance on syntax and best practices
4. **Template Context**: Available template variables and functions are undocumented, limiting template effectiveness

## What

Add comprehensive user documentation covering:

- **Pattern syntax guide**: Glob patterns, wildcards, recursive matching for categories/collections
- **MIME-multipart format**: When to use, how to enable, output format explanation
- **Template syntax reference**: Chevron basics with links to authoritative resources
- **Template context reference**: Complete variable and function reference organized by group

## How

Update existing documentation files with new sections covering these topics, ensuring users can effectively configure and use all available features.

## Success Criteria

- Users can configure file patterns without trial-and-error
- Users understand when and how to use MIME format
- Users can write effective templates using available context
- Documentation includes practical examples for each feature
