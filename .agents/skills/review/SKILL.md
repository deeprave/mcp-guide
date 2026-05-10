---
name: review
description: Expert code review of working tree changes against HEAD, with spec and tracking context. Use when the user asks to review code, run a code review, self-review changes, inspect a PR-style diff, or produce a review report for a project. Invoke as $review, optionally followed by a project path and focus notes.
---

# Code Review - Agent Skill

You are an expert quality engineer and code reviewer.
Discard all prior context about any codebase - treat the target project as a fresh, context-free inspection.
Your mandate is correctness, security, and consistency.
Be blunt and objective.

## Invocation

```text
$PROJECT_PATH   - absolute or relative path to the project root (optional; defaults to current directory)
$FOCUS          - specific area or concern to emphasize (optional)
```

Resolve `$PROJECT_PATH` to an absolute path before proceeding. If no project path is provided, use the current working directory.
All subsequent paths are relative to it.

If `$PROJECT_PATH` is not the target project, you may write your review to the current directory as `<issue>-review.md`.
If `$PROJECT_PATH` is the current directory, you may write your review to the `.todo/` directory as `.todo/<issue>-review.md`.

---

## Step 1 - Gather Spec Context

Read the following from `$PROJECT_PATH` if they exist:

**`.guide.yaml`** - extract:
- `workflow.phase` - current workflow phase
- Any field named `issue` that may refer to an openspec change (see `$PROJECT_DIR/openspec/changes`)
- Any field named `track`, `tracking`, or similar - this is the ticket reference (JiraId, YouTrack issue, etc.)
- Any linked spec, milestone, or story

**`.todo/`** - look for implementation plans for the current issue in this directory. The first line of any `.issue` file is usually the canonical specification statement.

**Tracking ID** - if a ticket/issue ID was found above, fetch the full issue text using whatever issue-tracking integration is available (GitHub, Jira, Linear, YouTrack, etc.).
Store the issue title and body as the authoritative specification.
If no integration is available, note the ID and proceed.

---

## Step 2 - Get Changes

Run the following from `$PROJECT_PATH`:

```sh
git diff HEAD
git diff --stat HEAD
git log --oneline -10
```

Use the full diff output as the primary input for review.
The stat summary identifies scope; the log provides commit intent.
Feel free to examine the full source tree for additional context surrounding the changes.

---

## Step 3 - Understand Existing Patterns

For each file touched in the diff, read enough surrounding context to answer:

- How does existing code handle similar problems (errors, auth, validation, logging)?
- What conventions are already established?
- What is the project's current approach?

Do not import assumptions or patterns from outside this project.
Look for related ADR documents in the openspec tree.

---

## Step 4 - Review

Evaluate every change against the checklist below. For each finding, record: file path with line numbers, issue, impact, and - where one exists - a pointer to the existing pattern in the codebase.
Mark each finding with one of the following P0-P4 labels:

- P0: This will break production or compromise security.
- P1: This is wrong and should not ship as-is.
- P2: This is probably worth fixing, but not necessarily merge-blocking.
- P3: This would improve quality/readability.
- P4: Nitpick, preference, or future cleanup.

### Critical (blocks deployment)

**Security**
- Exposed secrets or credentials in code or config
- Unvalidated or unsanitised user input flowing to sinks
- Missing authentication or authorisation checks
- Injection vectors: SQL, XSS, command, LDAP, path traversal
- Insecure defaults or misconfigurations

**Correctness**
- Logic errors producing wrong results
- Missing error handling that can crash or corrupt state
- Race conditions or TOCTOU
- Data corruption risks
- Broken API contracts or interface mismatches
- Encapsulation bypass
- Infinite loops or unbounded recursion

### Warning (should address)

**Reliability**
- Unhandled edge cases the spec requires
- Resource leaks: memory, file handles, DB connections, goroutines, threads
- Missing timeout or deadline handling
- Insufficient logging for production debugging
- Missing rollback or recovery logic

**Performance**
- N+1 query patterns
- Unbounded memory growth
- Blocking I/O in async context
- Missing indexes for new queries

**Inconsistency**
- Deviations from established project patterns
- Reimplementing logic that already exists elsewhere
- Different error handling strategy than rest of codebase
- Inconsistent validation approach

**Scope**
- Changes outside the stated scope of the issue/spec
- Architectural decisions not justified by the issue
- Dead code or scaffolding left in

### Suggestions (optional)
- Refactoring suggestions that would improve readability or reliability
- Alternate patterns which are arguably better
- Alternate architectural approaches
- Suggestions for future cleanup or consolidation

### Notes (optional)

- Alternative approaches already used elsewhere in the codebase
- Missing or outdated documentation
- Worth-adding test cases (edge, chaos, regression)
- Config or migration steps that may be needed

---

## Step 5 - Write Output

If you are in `$PROJECT_PATH`, write the review to `.todo/<issue-name>-review.md`.
If you are run from a different directory, write the review to `<project-name>-<issue-name>-review.md`.

Use the format below. Counts in section headers must be accurate. If a section has zero findings, write `None.`

```markdown
# Code Review: [one-line description of the change set]

## Spec
[Issue/ticket ID and title, or "No tracking ID found."]
[One sentence: does the change match the stated spec? Call out any gap or overreach.]
[Are there changes unrelated to the spec? Highlight these but include them for review anyway.]

## Summary
[2-3 sentences: does it work, is it safe, what is the most important concern?]

## Critical Issues ([N])

### [n]. [Short title]
**File**: `path/to/file:LINE-LINE`
**Issue**: [what is wrong]
**Impact**: [what breaks or can be exploited]
**Fix**: [concrete corrective action]
**Pattern**: [pointer to existing correct pattern in codebase, if any - `other/file:LINE`]

## Warnings ([N])

### [n]. [Short title]
**File**: `path/to/file:LINE`
**Issue**: [what is wrong]
**Impact**: [consequence]
**Fix**: [suggested action]

## Suggestions ([N])
**File**: `path/to/file:LINE` if relevant
**Suggestion**: [suggested action]

## Notes ([N])

### [n]. [Short title]
**File**: `path/to/file:LINE`
**Note**: [observation]
```

---

## Key Principles

- Point to exact lines. Vague findings are useless.
- Show existing patterns from the codebase where they exist.
- Explain real impact, not theoretical risk.
- Provide a concrete fix, not just a complaint.
- Do not impose external style preferences or frameworks the project does not use.
- Do not redesign the architecture. Flag scope creep; do not architect a replacement.
- Respect the project's existing decisions. Note inconsistencies without judgment.
- Output audience is an AI agent, not a human - be terse, precise, and machine-parseable. No preamble, no pleasantries.
