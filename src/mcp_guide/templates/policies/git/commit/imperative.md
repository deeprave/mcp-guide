---
type: agent/instruction
description: >
  Commit Policy: Imperative Style (Default). Commit messages follow the imperative mood convention with a structured body.
---
# Commit Policy: Imperative Style (Default)

Commit messages follow the imperative mood convention with a structured body.

## Format

```
<subject line — max 72 characters>

<body — optional but recommended>
```

## Subject line rules

- Imperative mood: "Add feature" not "Added feature" or "Adds feature"
- Capitalise the first letter
- No trailing period
- Describe what the change does, not how or why
- Prefix with tracking ID if known (e.g. `PROJ-123 Add feature`)
- Indicate change type (feature, bugfix, refactor, etc.)

## Body rules

- Separate from subject with a blank line
- Use dashes, not bullets
- Explain the what and why, not the how
- Small changes: subject line only
- Medium changes: brief body with context
- Large changes: detailed body with motivation and any breaking changes
- Bug fixes: describe what was broken and how it was fixed
- Omit test statistics, coverage details, and OpenSpec changes

## Rationale

Imperative mood matches git's own convention and reads naturally in `git log`.
Consistent format makes history scannable and tooling-friendly.
