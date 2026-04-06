---
type: agent/instruction
description: >
  PR Policy: GitHub Standard (Default). Pull request descriptions follow a structured four-section format.
---
# PR Policy: GitHub Standard (Default)

Pull request descriptions follow a structured four-section format.

## Format

```
<title — imperative mood, prefix with tracking ID if known>

<Overview>
Reason, rationale, or issue addressed by this pull request.

<Changes>
Concise description of functional changes made.
No file-level details; describe what changed behaviourally.

<Impact>
What is affected by this change.

<Notes>
Any additional context, caveats, or follow-on work.
```

## Rules

- Title in imperative mood, capitalised, no trailing period
- Prefix title with tracking ID if known
- Do not mention test statistics, coverage, or OpenSpec changes
- Focus on code changes, not documentation
- Use dashes for lists, not bullets

## Rationale

Consistent PR descriptions help reviewers understand the purpose and scope of a
change quickly. The four sections cover the most common reviewer questions.
