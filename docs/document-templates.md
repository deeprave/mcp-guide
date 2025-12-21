# Document Templates

MCP Guide serves documents that can be plain text, Markdown, or dynamic templates. While static documents work perfectly for most use cases, templates provide adaptability and dynamic content generation based on context, project configuration, and runtime data.

## Document Types

### Static Documents
Documents can be any text-based format:
- **Markdown** (`.md`) - Most common for documentation
- **Plain text** (`.txt`) - Simple text files
- **Code files** - Any programming language
- **Configuration files** - YAML, JSON, TOML, etc.

Static documents are served as-is without any processing.

### Template Documents
Templates are processed before serving, allowing dynamic content generation. MCP Guide supports multiple template extensions:

- **`.mustache`** - Standard Mustache template extension
- **`.hbs`** - Handlebars template extension (widely used)
- **`.handlebars`** - Alternative Handlebars extension
- **`.chevron`** - Chevron library specific extension

All template extensions use the same Mustache syntax and are processed identically.

## Template Syntax

MCP Guide uses the [Chevron](https://github.com/noahmorrison/chevron) library, which implements the [Mustache templating language](http://mustache.github.io). Mustache is a logic-less template system that works by expanding tags in a template using values provided in a context object.

### Basic Variables
```mustache
Hello, {{name}}!
Project: {{project.name}}
```

### Conditionals
```mustache
{{#user}}
  Welcome back, {{name}}!
{{/user}}

{{^user}}
  Please log in.
{{/user}}
```

### Loops
```mustache
{{#project.categories}}
  - {{.}}
{{/project.categories}}

{{#files}}
  File: {{path}} ({{size}} bytes)
{{/files}}
```

### Comments
```mustache
{{! This is a comment and won't appear in output }}
```

### Lambda Functions
MCP Guide provides built-in lambda functions for advanced formatting:

```mustache
{{#format_date}}%B %d, %Y{{file.mtime}}{{/format_date}}
{{#truncate}}50{{description}}{{/truncate}}
{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}
```

## Template Context Variables

Templates have access to a rich context hierarchy with the following variables:

### System Context
- `timestamp` - Current Unix timestamp (float)
- `timestamp_ms` - Current timestamp in milliseconds (float)
- `timestamp_ns` - Current timestamp in nanoseconds (integer)
- `now.date` - Current local date (YYYY-MM-DD)
- `now.day` - Current day name (e.g., "Monday")
- `now.time` - Current local time (HH:MM)
- `now.tz` - Local timezone offset
- `now.datetime` - Full local datetime string
- `now_utc.*` - Same fields but in UTC

### Agent Context
- `@` - Agent prompt character (e.g., "guide", "/", "@")
- `agent.name` - Agent name from MCP session
- `agent.version` - Agent version
- `agent.prompt_prefix` - Agent prompt prefix
- `tool_prefix` - MCP tool prefix with underscore (e.g., "guide_", "custom_")

### Project Context
- `project.name` - Project name
- `project.created_at` - Project creation timestamp (ISO 8601)
- `project.updated_at` - Project last update timestamp (ISO 8601)
- `project.categories` - Array of category names
- `project.collections` - Array of collection names

### Category Context (when applicable)
- `category.name` - Category name
- `category.dir` - Category directory path (relative to docroot)
- `category.description` - Category description (if set)

### Collection Context (when accessed via collection)
- `collection.name` - Collection name
- `collection.categories` - Array of category patterns in the collection
- `collection.description` - Collection description (if set)

### File Context
- `file.path` - Relative path from category directory
- `file.basename` - Filename without template extension
- `file.category` - Category name where file is located
- `file.collection` - Collection name (if accessed via collection)
- `file.size` - File size in bytes (rendered content size for templates)
- `file.mtime` - File modification time (ISO 8601)
- `file.ctime` - File creation time (ISO 8601, if available)

### Feature Flags
Feature flags are resolved in hierarchical order (project flags override global flags):

```mustache
{{#flags.enable_advanced_features}}
  Advanced content here...
{{/flags.enable_advanced_features}}

{{^flags.hide_experimental}}
  Experimental features...
{{/flags.hide_experimental}}
```

## Front Matter

Templates can include YAML front matter to provide metadata and context to the agent:

```yaml
---
title: "API Documentation"
description: "Complete API reference for the project"
tags: ["api", "reference", "documentation"]
audience: "developers"
difficulty: "intermediate"
---

# {{title}}

This {{description}} covers...
```

Front matter is processed and made available in the template context under the `frontmatter` key:

```mustache
# {{frontmatter.title}}

Difficulty: {{frontmatter.difficulty}}

{{#frontmatter.tags}}
- {{.}}
{{/frontmatter.tags}}
```

## Template Examples

### Project Overview Template
```mustache
---
title: "{{project.name}} Overview"
description: "Project overview generated on {{now.date}}"
---

# {{project.name}} Project

**Generated:** {{now.datetime}}
**Categories:** {{project.categories.length}}
**Collections:** {{project.collections.length}}

## Categories
{{#project.categories}}
- **{{.}}** - {{category.description}}
{{/project.categories}}

## Recent Activity
Last updated: {{#format_date}}%B %d, %Y at %H:%M{{project.updated_at}}{{/format_date}}
```

### Dynamic Tool Reference Template
```mustache
# Available Tools

Use the following MCP tools in your workflow:

- `{{tool_prefix}}get_content` - Retrieve content from categories or collections
- `{{tool_prefix}}list_categories` - List all available categories
- `{{tool_prefix}}add_category` - Add a new category

{{#flags.enable_advanced_tools}}
## Advanced Tools
- `{{tool_prefix}}clone_project` - Clone project configuration
{{/flags.enable_advanced_tools}}
```

### File Listing Template
```mustache
# Files in {{category.name}}

{{#files}}
## {{file.basename}}

- **Path:** `{{file.path}}`
- **Size:** {{file.size}} bytes
- **Modified:** {{#format_date}}%B %d, %Y{{file.mtime}}{{/format_date}}

{{#file.description}}
{{file.description}}
{{/file.description}}

---
{{/files}}
```

## Resources

### Documentation
- [Mustache Manual](http://mustache.github.io/mustache.5.html) - Official Mustache specification
- [Handlebars Guide](https://handlebarsjs.com/guide/) - Handlebars documentation (superset of Mustache)
- [Chevron GitHub](https://github.com/noahmorrison/chevron) - Python Mustache implementation used by MCP Guide

### Online Tools
- [Mustache Try Online](http://mustache.github.io/#demo) - Test Mustache templates online
- [Handlebars Try Online](https://handlebarsjs.com/playground.html) - Interactive Handlebars playground

### Template Best Practices
1. **Keep logic minimal** - Mustache is intentionally logic-less
2. **Use descriptive variable names** - Make templates self-documenting
3. **Leverage front matter** - Provide context and metadata for agents
4. **Test with different contexts** - Ensure templates work across projects
5. **Use feature flags** - Make content conditional based on configuration
6. **Document template variables** - Comment expected context structure

## Feature Flags in Templates

Feature flags provide conditional content based on project or global configuration:

### Setting Flags
```bash
# Global flags (affect all projects)
guide set_feature_flag enable_advanced_features true
guide set_feature_flag api_version "v2"

# Project flags (override global)
guide set_project_flag hide_experimental false
guide set_project_flag custom_branding true
```

### Using Flags in Templates
```mustache
{{#flags.enable_advanced_features}}
# Advanced Features

{{#flags.api_version}}
API Version: {{flags.api_version}}
{{/flags.api_version}}

{{#flags.custom_branding}}
![Custom Logo]({{project.logo_url}})
{{/flags.custom_branding}}
{{/flags.enable_advanced_features}}

{{^flags.hide_experimental}}
⚠️ **Experimental:** This feature is in beta.
{{/flags.hide_experimental}}
```

### Flag Resolution
Flags are resolved hierarchically:
1. **Project flags** (highest priority)
2. **Global flags** (fallback)
3. **Default values** (if flag not set)

This allows global defaults with project-specific overrides, enabling consistent behavior across projects while allowing customization where needed.
