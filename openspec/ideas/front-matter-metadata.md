# Front Matter Metadata Support

## Overview
Add YAML front matter support to template files, enabling rich metadata extraction for both template rendering and agent intelligence while maintaining clean content output.

## Concept
Files can include YAML front matter at the beginning, which gets:
1. **Parsed** and removed from rendered content
2. **Used** as highest-priority template context
3. **Exposed** to agents via Result metadata for intelligent processing

## Example Usage

### Input File
```yaml
---
title: "OAuth 2.0 Authentication Guide"
description: "Complete guide to implementing OAuth 2.0 authentication"
author: "Development Team"
difficulty: "intermediate"
topic: "security"
last_updated: "2024-12-14"
prerequisites: ["basic-auth", "jwt-tokens"]
estimated_reading_time: "15 minutes"
status: "published"
---
# {{title}}

{{description}}

**Author:** {{author}}
**Difficulty:** {{difficulty}}
**Last Updated:** {{last_updated}}

## Prerequisites
{{#prerequisites}}
- {{.}}
{{/prerequisites}}

[Content continues...]
```

### Rendered Output
```markdown
# OAuth 2.0 Authentication Guide

Complete guide to implementing OAuth 2.0 authentication

**Author:** Development Team
**Difficulty:** intermediate
**Last Updated:** 2024-12-14

## Prerequisites
- basic-auth
- jwt-tokens

[Content continues...]
```

### Agent Metadata
```json
{
  "front_matter": {
    "title": "OAuth 2.0 Authentication Guide",
    "description": "Complete guide to implementing OAuth 2.0 authentication",
    "author": "Development Team",
    "difficulty": "intermediate",
    "topic": "security",
    "last_updated": "2024-12-14",
    "prerequisites": ["basic-auth", "jwt-tokens"],
    "estimated_reading_time": "15 minutes",
    "status": "published"
  },
  "template_rendered": true,
  "file_info": {...}
}
```

## Technical Implementation

### Front Matter Detection & Parsing
```python
def has_front_matter(content: str) -> bool:
    """Check if content starts with YAML front matter."""
    return content.startswith('---\n')

def extract_front_matter(content: str) -> tuple[dict, str]:
    """Extract YAML front matter and return metadata + clean content."""
    if not has_front_matter(content):
        return {}, content

    lines = content.split('\n')
    end_idx = None

    # Find closing ---
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return {}, content  # Malformed, treat as regular content

    yaml_content = '\n'.join(lines[1:end_idx])
    remaining_content = '\n'.join(lines[end_idx + 1:])

    try:
        metadata = yaml.safe_load(yaml_content) or {}
        return metadata, remaining_content
    except yaml.YAMLError:
        return {}, content  # Invalid YAML, treat as regular content
```

### Template Context Integration
```python
def render_file_content(file_info: FileInfo, context: TemplateContext | None = None) -> Result[str]:
    """Render file content with front matter support."""
    # Extract front matter if present
    metadata, clean_content = extract_front_matter(file_info.content)

    # Create front matter context layer (highest priority)
    if metadata:
        front_matter_context = TemplateContext(metadata)
        context = front_matter_context.new_child(context) if context else front_matter_context

    # Update file_info with clean content for rendering
    file_info.content = clean_content

    # Render template with enhanced context
    rendered = render_template(clean_content, context)

    # Return with metadata for agent intelligence
    return Result.ok(
        value=rendered,
        metadata={
            "front_matter": metadata,
            "template_rendered": True,
            "file_info": file_info.to_dict()
        }
    )
```

### Result Enhancement
```python
@dataclass
class Result(Generic[T]):
    """Result pattern with metadata support."""
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    exception: Optional[Exception] = field(default=None, repr=False, compare=False)
    message: Optional[str] = None
    instruction: Optional[str] = None
    error_data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None  # NEW: For structured metadata
```

## Context Precedence
With front matter, template context precedence becomes:
```
Front Matter (highest priority)
↓
File Context
↓
Category Context
↓
Project Context
↓
Agent Context
↓
System Context (lowest priority)
```

## Agent Intelligence Benefits

### Content Understanding
- **Topic classification**: Route questions based on `topic` field
- **Difficulty matching**: Suggest appropriate complexity level
- **Status awareness**: Handle draft/deprecated content appropriately
- **Prerequisite checking**: Guide users through learning paths

### Smart Filtering
- **Relevance scoring**: Use metadata for better content ranking
- **Freshness detection**: Prioritize recently updated content
- **Audience targeting**: Match content to user expertise level
- **Content type routing**: Handle tutorials vs. references differently

### Enhanced Responses
```python
# Agent can provide richer context
if metadata.get("difficulty") == "advanced":
    response += "\n\n⚠️ This is advanced content. Consider reviewing prerequisites first."

if metadata.get("status") == "draft":
    response += "\n\n📝 Note: This content is in draft status and may be incomplete."

if prerequisites := metadata.get("prerequisites"):
    response += f"\n\n📚 Prerequisites: {', '.join(prerequisites)}"
```

## Format Impact Analysis

### MIME Format
- **No structural change**: Front matter becomes part of each file's content
- **Content-Length**: Includes front matter bytes in calculations
- **Headers unchanged**: Standard MIME multipart structure preserved

### Plain Format
- **Potential separator collision**: Current `--- filename ---` vs YAML `---`
- **Solution options**:
  - Use different separators (e.g., `=== filename ===`)
  - Escape/detect YAML blocks specially
  - Format-aware handling

## Implementation Complexity

### Advantages
- **Simple parsing**: YAML well-supported with PyYAML
- **Existing patterns**: Template context layering already implemented
- **Minimal changes**: Add front matter layer to context chain
- **Graceful degradation**: Files without front matter work unchanged
- **Standard format**: YAML front matter widely recognized

### Dependencies
- **PyYAML**: Standard Python YAML library
- **~20-30 lines**: Minimal parsing logic required
- **No breaking changes**: Backward compatible with existing files

### Risk Assessment
- **Very low risk**: Well-established patterns and libraries
- **Easy testing**: Simple to validate and test
- **Incremental adoption**: Can be added gradually to existing content

## Use Cases

### Documentation Management
```yaml
---
title: "API Reference"
version: "2.1.0"
audience: "developers"
last_reviewed: "2024-12-01"
reviewers: ["alice", "bob"]
---
```

### Content Organization
```yaml
---
category: "tutorials"
subcategory: "authentication"
tags: ["oauth", "security", "api"]
related_docs: ["jwt-guide.md", "api-keys.md"]
---
```

### Template Customization
```yaml
---
template_style: "detailed"
show_examples: true
include_troubleshooting: true
code_language: "python"
---
```

### Workflow Management
```yaml
---
status: "draft"
assignee: "john.doe"
due_date: "2024-12-20"
review_required: true
---
```

## Future Enhancements

### Validation
- Schema validation for front matter fields
- Required field enforcement
- Type checking for metadata values

### Indexing
- Build searchable index from front matter
- Enable metadata-based queries
- Support faceted search

### Automation
- Auto-generate metadata from content analysis
- Workflow triggers based on status changes
- Content freshness monitoring

## Benefits Summary

1. **Clean Content**: Front matter removed from rendered output
2. **Rich Context**: Metadata available for template variables
3. **Agent Intelligence**: Structured data for smart responses
4. **Standard Format**: Widely recognized YAML front matter
5. **Backward Compatible**: Existing files continue to work
6. **Extensible**: Easy to add new metadata fields
7. **Minimal Implementation**: Low complexity, high value

This approach provides a powerful foundation for content metadata while maintaining simplicity and compatibility with existing systems.
