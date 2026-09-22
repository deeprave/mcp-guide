---
cache: long
---

# Guide Skill Authoring Reference

This README is a repository reference for people maintaining bundled Guide
skill packages.

## Package Layout

Each bundled skill is a direct child of `_skills/`:

```text
_skills/
  <skill-name>/
    SKILL.md.mustache
    resources/        # optional readable package resources
    scripts/          # optional agent-run scripts
    agents/           # optional agent definitions
```

`SKILL.md.mustache` is the public entrypoint for each skill. Its package name becomes the
skill identifier and resource URI, for example `git-commit` becomes
`guide://$git-commit`.

## Required Entrypoint Metadata

Every entrypoint must provide these frontmatter fields:

```yaml
name: <skill-name>
description: <concise capability description>
usage: <when an agent should use this skill>
```

Use `cache: short, private` for workflow guidance whose content depends on
project configuration or current workflow state. Add an `elicitation` block
only when a user selection is genuinely required before the instructions can
be rendered.

## Policy-Aware Skills

Declare each policy topic the skill consumes in its frontmatter and render the
matching partial in the body:

```yaml
policies: [git/delivery, issue-tracking]
```

```mustache
{{> git/delivery}}
{{> issue-tracking}}
```

When a public Guide skill is rendered, Guide gathers only the project's
selected documents for each declared topic. A skill must render every declared
topic; declaring a topic without its partial leaves the selected policy
ineffective.

## Writing Instructions

Use a concise title and clear sections such as `## Directives` and
`## Selected Policies` for operational guidance. Refer to another bundled
skill as Guide skill `<skill-name>` so the intended skill boundary is
discoverable to MCP-capable agents.
