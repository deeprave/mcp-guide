# Guide Skills Authoring

Guide skills are server-owned, native-skill-shaped packages in the configured document root:

```text
_skills/
  workflow/
    review/
      SKILL.md.mustache
```

The package directory may be nested for organisation. Its directory is private implementation detail;
the public entrypoint is the required frontmatter `name`, so this example remains
`guide://$workflow-review`. A skill package may include
`references/`, `scripts/`, or `agents/` members, which are retrieved individually through the same
skill URI root. `SKILL.md` is the entrypoint and contains the instructions an agent follows.

## Skill Frontmatter

Every skill entrypoint declares at least `name`, `description`, and `usage` in YAML frontmatter:

```yaml
---
name: workflow-review
description: Review a selected change and present the findings.
usage: Use when the user asks to review a change.
---
```

The normal document frontmatter fields, including `type`, `instruction`, `requires-*`, `cache`,
and template variables, apply to skills. Bundled skills omit `type`; their entrypoint delivery
defaults to `agent/instruction`.

Skill names are global identifiers within one Guide runtime and must be unique. Missing, invalid,
or duplicate names make the affected package unavailable and produce a server warning. A
`requires-*` declaration controls availability for each session after Guide has discovered the
shared package catalogue; it does not change the package's public identity.

## Elicitation

Skills use the shared elicitation contract. See [Elicitation Authoring](authoring-elicitation.md)
for the complete declaration reference, branching behaviour, protocol differences, and examples.

## Security and Execution

Scripts are delivered as content only. Guide does not execute a script from a skill package. A
client that chooses to download and execute one does so locally and must treat it as untrusted until
it has been inspected.
