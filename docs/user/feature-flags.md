# Feature Flags

Feature flags control how mcp-guide behaves, what features are enabled, and how content is delivered. You can set flags globally (affecting all projects) or per-project (for specific contexts).

## Viewing Flags

Use the `@guide :flags` prompt command to see what's currently active. It shows feature flags, project flags, and the resolved values (what's actually in effect).

**See:** [Commands](commands.md) for more on the `:flags` command.

## How Flags Work

Flags can be set at two levels:

**Project flags** - Apply to a specific project. Just ask your AI agent:

```
Please set the workflow feature flag to true for this project
```

**Feature flags** - Apply across all projects by default. Ask your AI agent:

```
Please set the content-format feature flag to mime globally
```

When resolving what value to use, project flags take precedence over feature flags, which take precedence over defaults.

## Setting Flags

Just ask your AI agent using natural language:

```
Set the workflow flag to true
Enable OpenSpec for this project
Set content-style to plain globally
Remove the workflow flag (use default)
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
| `allow-client-info` | Enables collection of client environment information (OS, hostname, user, git remotes). Privacy-sensitive. | `boolean` | `false` |
| `guide-development` | Enables development features for mcp-guide itself. | `boolean` | `false` |

**Notes:**

- `workflow` set to `true` enables all 5 default phases: discussion, planning, implementation, check, review
- `workflow` can be a list to enable specific phases: `["discussion", "planning", "implementation"]` (`discussion` and `implementation` are mandatory)
- `workflow-consent` set to `true` applies default consent: implementation requires entry consent, review requires exit consent
- `workflow-consent` can be a dict for custom consent: `{"planning": ["entry"], "implementation": ["entry", "exit"]}`

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

