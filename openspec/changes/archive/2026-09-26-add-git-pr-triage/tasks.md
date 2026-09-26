# Tasks

## 1. Skill package and invocation contract

- [x] 1.1 Add the bundled `git-pr-triage` skill package, metadata, and user-facing invocation guidance; verify it is discoverable through the Guide skill catalogue with Git skills available independently of workflow and OpenSpec modes.
- [x] 1.2 Define selection precedence for a supplied pull-request URL or number, an active contextual pull request, and current-branch fallback; verify missing or mismatched context asks the user without creating review state.

## 2. Review feedback analysis and durable state

- [x] 2.1 Implement collation guidance for inline threads, review summaries, and review-related issue comments using GitHub MCP first and a disclosed `gh` fallback; verify production-facing tests cover both guidance paths and a concern represented on multiple surfaces.
- [x] 2.2 Implement `{{path.documents}}`-relative seen-comment state using stable provider identifiers, deterministic fallback keys, and concern fingerprints; verify production-facing tests cover newly reported, previously seen, repeated-concern, and failed-report cases.
- [x] 2.3 Implement grouped finding classification, current diff and source applicability checks, and concise action recommendations; verify duplicate, stale, and actionable feedback are distinguished through delivered behaviour.

## 3. Presentation preference and validation

- [x] 3.1 Implement grouped reporting as the default and recommend `just-one` only when the user chooses sequential triage; verify the production skill guidance never invokes or implies sequential triage without that preference.
- [x] 3.2 Update relevant skill authoring or user documentation and verify examples preserve the analysis-only, no-implementation boundary.
- [x] 3.3 Run focused pytest coverage, Ruff and type checks, strict OpenSpec validation for `add-git-pr-triage`, and `git diff --check`; record any full-suite result or environmental blocker.
