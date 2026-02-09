# Feature Flags

Understanding and using feature flags in mcp-guide.

## What are Feature Flags?

Feature flags control mcp-guide behavior and enable conditional content inclusion. They can be set globally or per-project.

## Flag Scope

### Project Flags

Set for a specific project:

```bash
# Via MCP tool
set_project_flag(feature_name="workflow", value=True)
```

Stored in: `~/.config/mcp-guide/projects/<project>/config.yaml`

### Global Flags

Set across all projects:

```bash
# Via MCP tool
set_feature_flag(feature_name="content-style", value="mime")
```

Stored in: `~/.config/mcp-guide/config.yaml`

### Resolution

When resolving flags:
1. Check project flags first
2. Fall back to global flags
3. Use default if not set

## Setting Flags

### Via MCP Tools

```python
# Set project flag
set_project_flag(feature_name="workflow", value=True)

# Set global flag
set_feature_flag(feature_name="content-style", value="plain")

# Remove flag (use default)
set_project_flag(feature_name="workflow", value=None)
```

### Via Configuration Files

**Project** (`~/.config/mcp-guide/projects/<project>/config.yaml`):

```yaml
flags:
  workflow: true
  openspec: true
```

**Global** (`~/.config/mcp-guide/config.yaml`):

```yaml
flags:
  content-style: mime
```

## Querying Flags

```python
# Get project flag (with fallback to global)
get_project_flag(feature_name="workflow")

# Get global flag only
get_feature_flag(feature_name="content-style")

# List all active flags
list_project_flags(active=True)
```

## Special Flags

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

```yaml
flags:
  workflow: true
```

### workflow-file

Path to workflow tracking file.

**Type**: String
**Default**: `.guide.yaml`
**Scope**: Project
**Requires**: `workflow: true`

**Usage**:

```yaml
flags:
  workflow: true
  workflow-file: .workflow.yaml
```

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

```yaml
flags:
  workflow: true
  workflow-consent: true
```

### openspec

Enables OpenSpec integration.

**Type**: Boolean
**Default**: `false`
**Scope**: Project

**When enabled**:
- Provides OpenSpec workflow instructions
- Integrates with `openspec/` directory
- Adds OpenSpec-specific tools

**Usage**:

```yaml
flags:
  openspec: true
```

**See**: [OpenSpec documentation](https://openspec.dev)

### content-style

Output format for content delivery.

**Type**: String
**Values**: `None`, `plain`, `mime`
**Default**: `None`
**Scope**: Global or Project

**Values**:
- `None` - Raw content (default)
- `plain` - Plain text formatting
- `mime` - MIME multipart format

**Usage**:

```yaml
flags:
  content-style: mime
```

**MIME format** is useful for:
- Structured content delivery
- Multiple content types
- Client-side parsing

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

Document is included only if `workflow` flag is `true`.

### Multiple Conditions

```yaml
---
requires-workflow: true
requires-openspec: true
---

Content requires both flags...
```

### Value Matching

```yaml
---
requires-content-style: mime
---

Content for MIME format only...
```

### List Matching

```yaml
---
requires-languages: python
---

Python-specific content...
```

If `languages` flag is a list, document is included if list contains "python".

## Flag Patterns

### Development Workflow

```yaml
flags:
  workflow: true
  workflow-consent: true
  openspec: true
```

### Production Deployment

```yaml
flags:
  content-style: mime
  workflow: false
```

### Language-Specific

```yaml
flags:
  languages:
    - python
    - typescript
  frameworks:
    - fastapi
    - react
```

## Best Practices

### Flag Design

- **Boolean for features** - Use true/false for feature toggles
- **Strings for options** - Use strings for configuration values
- **Lists for sets** - Use lists for multiple values
- **Descriptive names** - Use clear, descriptive flag names

### Flag Usage

- **Project-specific** - Use project flags for project settings
- **Global defaults** - Use global flags for common settings
- **Document flags** - Document custom flags in project README
- **Test combinations** - Test with different flag combinations

### Content Gating

- **Explicit requirements** - Use `requires-*` for conditional content
- **Fail gracefully** - Content should work without flags when possible
- **Document dependencies** - Note which flags are required

## Troubleshooting

### Flag Not Working

Check:
1. Flag is set correctly (spelling, case)
2. Scope is correct (project vs global)
3. Value type matches (boolean, string, list)

### Content Not Included

Verify:
1. `requires-*` matches flag name
2. Flag value matches requirement
3. Flag is set in correct scope

### Flag Not Persisting

Ensure:
1. Configuration file is writable
2. YAML syntax is valid
3. Using correct tool (project vs global)

## Next Steps

- **[Content Documents](content-documents.md)** - Using flags in templates
- **[Workflows](../developer/workflows.md)** - Workflow flag details
- **[Content Management](content-management.md)** - Conditional content

