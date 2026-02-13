# Feature Flags

mcp-guide uses feature flags to control behaviour, enable optional features, and customise content delivery. Flags can be set globally (all projects) or per-project, providing flexible configuration for different development contexts.

## Viewing Flags

Use the `:flags` command to see all active flags:

```
:flags
```

Shows:
- Feature (global) flags
- Project flags
- Resolved values (feature flags that are actually active)

**See:** [Commands](commands.md) for detailed information on the `:flags` command.

## Overview

### Project Flags

Set for a specific project. Ask your AI agent to set project flags:

```
Please set the workflow feature flag to true for this project
```

### Global Flags

Set across all projects. Ask your AI agent to set global flags:

```
Please set the content-format feature flag to mime globally
```

### Resolution

When resolving flags:
1. Check project flags first
2. Fall back to global flags
3. Use default if not set

## Setting Flags

Ask your AI agent to set flags using natural language:

```
Set the workflow flag to true
Enable OpenSpec for this project
Set content-style to plain globally
Remove the workflow flag (use default)
```

## Core Feature Flags

### workflow

Enables workflow phase tracking.

**Type**: Boolean
**Default**: `false`
**Scope**: Project

**When enabled**:
- Tracks development phases (discussion, planning, implementation, check, review)
- Provides phase-specific instructions
- Enforces phase transition rules

**Usage**:

### workflow-file

Path to workflow tracking file.

**Type**: String
**Default**: `.guide.yaml`
**Scope**: Project
**Requires**: `workflow: true`

### workflow-consent

Controls phase transition consent requirements.

**Type**: Boolean
**Default**: `true`
**Scope**: Project
**Requires**: `workflow: true`

**When enabled**:
- Explicit consent required for implementation phase
- Explicit consent required to exit review phase

**Usage**:

### openspec

Enables OpenSpec integration.

**Type**: Boolean
**Default**: _false_
**Scope**: Project

**When enabled**:
- Provides OpenSpec workflow instructions
- Integrates with `openspec/` directory
- Adds OpenSpec-specific commands

**Usage**:

**See**: [OpenSpec documentation](https://openspec.dev)

### content-style

Controls how markdown formatting is rendered in template output for agent display.

**Type**: String
**Values**: `plain`, `headings`, `full`
**Default**: `plain`
**Scope**: Global or Project

**Why this matters:**

Different agents have varying capabilities for rendering markdown in their console or interface. Some agents display markdown beautifully with proper formatting, while others show raw markdown syntax which can be distracting or hard to read.

**How it works:**

Templates use variables to represent markdown formatting:
- `{{h1}}` through `{{h6}}` - Heading markers (e.g., `#`, `##`, `###`)
- `{{b}}` - Bold markers (`**`)
- `{{i}}` - Italic markers (`*`)

The `content-style` flag controls what these variables render as:

**`plain` (default)** - No formatting:
- All variables render as empty strings
- Output is plain text without markdown syntax
- Best for: Agents that don't render markdown well, or when clean text is preferred
- Example: `{{h2}}Status` renders as `Status`

**`headings`** - Heading markers only:
- `{{h1}}` through `{{h6}}` render as `#`, `##`, `###`, etc.
- `{{b}}` and `{{i}}` remain empty
- Best for: Agents that handle headings well but struggle with inline formatting
- Example: `{{h2}}Status` renders as `## Status`

**`full`** - All formatting:
- All variables render their markdown equivalents
- Complete markdown formatting in output
- Best for: Agents with excellent markdown rendering capabilities
- Example: `{{h2}}Status: {{b}}Active{{b}}` renders as `## Status: **Active**`

**Template example:**

```mustache
{{h1}}Project Information

{{h2}}Current Phase
{{b}}Phase:{{b}} {{workflow.phase}}
{{b}}Issue:{{b}} {{workflow.issue}}

{{h3}}Description
{{i}}Implementation in progress{{i}}
```

With `content-style: plain`:
```
Project Information

Current Phase
Phase: implementation
Issue: add-feature-x

Description
Implementation in progress
```

With `content-style: headings`:
```
# Project Information

## Current Phase
Phase: implementation
Issue: add-feature-x

### Description
Implementation in progress
```

With `content-style: full`:
```
# Project Information

## Current Phase
**Phase:** implementation
**Issue:** add-feature-x

### Description
*Implementation in progress*
```

**Choosing the right mode:**

- Start with `plain` (default) and only change if needed
- Try `headings` if your agent renders headings nicely but inline formatting looks cluttered
- Use `full` if your agent has excellent markdown support and you want rich formatting
- Consider your agent's console/interface capabilities
- Test different modes to see what works best for your workflow

## Using Flags in Templates

### Conditional Content

Use `requires-*` in frontmatter:

```yaml
---
requires-workflow: true
---

# Workflow Instructions

Follow the {{workflow.phase}} phase guidelines...
```
Document is included only if `workflow` flag is set and not false.

## Next Steps

- **[Content Documents](content-documents.md)** - Using flags in templates
- **[Workflows](workflows.md)** - Workflow flag details
- **[Content Management](content-management.md)** - Conditional content

