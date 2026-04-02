# Feature Flags

Feature flags control how mcp-guide behaves, what features are enabled, and how content is delivered. You can set flags globally (affecting all projects) or per-project (for specific contexts).

## Viewing Flags

Use the `@guide :flags` commands to view and manage flags:

```
@guide :flags                           # Show all flags with available commands
@guide :flags/list                      # List all flags (project and feature)
@guide :flags/project/list              # List project-specific flags
@guide :flags/feature/list              # List feature flags (global)
```

**See:** [Commands](commands.md) for complete flag command reference.

## How Flags Work

Flags can be set at two levels:

**Project flags** - Apply to a specific project:

```
@guide :flags/project/set workflow
@guide :flags/project/set workflow false
@guide :flags/project/set content-style --value=plain
@guide :flags/project/remove workflow      # Remove override, use feature flag value
```

**Feature flags** - Apply across all projects by default:

```
@guide :flags/feature/set workflow
@guide :flags/feature/set content-format --value=mime
@guide :flags/feature/remove autoupdate    # Remove flag entirely
```

When resolving what value to use, project flags take precedence over feature flags, which take precedence over defaults.

## Managing Flags

Use the flag commands to get, set, and remove flags:

```
# Get flag values
@guide :flags/project/get workflow
@guide :flags/feature/get autoupdate

# Set flag values
@guide :flags/project/set workflow true
@guide :flags/feature/set content-format --value=mime

# Remove flags
@guide :flags/project/remove workflow      # Revert to feature flag value
@guide :flags/feature/remove autoupdate    # Remove flag entirely
```

## Core Feature Flags

| Flag | Description | Type | Default |
|------|-------------|------|---------|
| `workflow` | Enables workflow phase tracking (discussion, planning, implementation, check, review). Can be `true` (all phases), `false` (disabled), or list of phase names. | `boolean` or `list[string]` | `false` |
| `workflow-file` | Path to workflow tracking file. Supports variables: `{project-name}`, `{project-key}`, `{project-hash}`. | `string` | `.guide.yaml` |
| `workflow-consent` | Controls phase transition consent requirements. Can be `true` (default consent rules), `false` (no consent required), or custom rules specifying which phases require consent to enter or exit. | `boolean` or `dict` | `true` |
| `openspec` | Enables OpenSpec integration for structured change management. Adds OpenSpec-specific commands and workflow instructions. | `boolean` | `false` |
| `startup-instruction` | Content expression to load when project session starts. Queued as high-priority instruction for immediate agent context. Supports any valid content expression (collection, category, or pattern). | `string` | (not set) |
| `content-style` | Controls markdown formatting in template output. `plain` = strips all formatting, `headings` = renders heading markers only, `full` = renders all markdown. | `string` | `plain` |
| `content-format` | Controls content MIME type. `text` = plain text, `mime` = MIME multipart format. | `string` | `text` |
| `path-documents` | Directory path for workflow tracking documents (plans, checklists, summaries). Supports both relative (`.todo/`) and absolute (`~/.goose/projects/knowledge/`) paths. Auto-added to `allowed_write_paths`. | `string` | `.todo/` |
| `path-export` | Directory path for exported knowledge content. Agent-specific defaults: Goose uses `~/.goose/projects/{project-hash}/knowledge/`, others use `.kiro/knowledge/`. Auto-added to `allowed_write_paths`. | `string` | (agent-specific) |
| `allow-client-info` | Enables collection of client environment information (OS, hostname, user, git remotes). Privacy-sensitive. | `boolean` | `false` |
| `autoupdate` | Enables automatic update prompting at startup when new documentation versions are available. Prompts agent to run the `update_documents` tool. Global only (cannot be set per-project). | `boolean` | `false` |
| `guide-development` | Enables development features for mcp-guide itself. | `boolean` | `false` |
| `content-accessor` | Controls how template `{{#resource}}` references are rendered. When `false` (default), renders as `guide://` URIs. When `true`, renders as tool calls using the configured tool prefix. Useful for agents that access content exclusively through tools. | `boolean` | `false` |

**Notes:**

- `workflow` set to `true` enables all 5 default phases: discussion, planning, implementation, check, review
- `workflow` can be a list to enable specific phases: `["discussion", "planning", "implementation"]` (`discussion` and `implementation` are mandatory)
- `workflow-consent` set to `true` applies default consent: implementation requires entry consent, review requires exit consent
- `workflow-consent` can be a dict for custom consent: `{"planning": ["entry"], "implementation": ["entry", "exit"]}`
- `path-documents` and `path-export` accept both relative paths (`.todo/`) and absolute paths (`/tmp/knowledge/`, `~/.goose/knowledge/`)
- Path flags automatically add trailing slash if missing and normalize backslashes to forward slashes
- Path flags are validated for security: path traversal (`../`, `..\\`) is blocked
- For absolute paths, system directories (`/etc`, `/sys`, `/proc`) are blocked
- Resolved path flag values are automatically added to `allowed_write_paths` for security policy compliance

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

- **[Documents](documents.md)** - Using flags in templates
- **[Workflows](workflows.md)** - Workflow flag details
- **[Content Management](content-management.md)** - Conditional content

