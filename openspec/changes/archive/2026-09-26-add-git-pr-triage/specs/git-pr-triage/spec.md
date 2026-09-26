# Spec Delta

## Purpose

Provide a durable, analysis-only Guide skill for triaging pull-request review
feedback without repeatedly examining comments that were already reported.

## ADDED Requirements

### Requirement: Git PR triage skill analyses selected pull-request feedback
The system SHALL serve `git-pr-triage` as a bundled Guide skill. It SHALL use
an explicitly supplied pull-request URL or number, an active contextual pull
request, or the current branch's pull request in that order. It SHALL retrieve
and collate inline review threads, review summaries, and review-related issue
comments, and inspect sufficient current diff and source context to assess
whether each concern still applies. It SHALL produce analysis and
recommendations only and SHALL NOT modify pull-request code, review comments,
or their resolution state.

#### Scenario: Supplied pull request is triaged
- **WHEN** a user selects `git-pr-triage` with a valid pull-request URL or
  number for the current repository
- **THEN** the skill SHALL direct the agent to analyse all available review
  feedback against current pull-request context
- **AND** it SHALL report recommendations without implementing changes

#### Scenario: Context provides the pull request
- **WHEN** no pull request is supplied and the active task context identifies
  a pull request for the current repository
- **THEN** the skill SHALL use that contextual pull request
- **AND** it SHALL not ask the user to identify it again

#### Scenario: Pull request cannot be identified
- **WHEN** no supplied, contextual, or current-branch pull request can be identified
- **THEN** the skill SHALL direct the agent to report that no pull request was
  identified and ask the user to provide one
- **AND** it SHALL NOT create review state

#### Scenario: GitHub MCP is unavailable
- **WHEN** GitHub review data is unavailable from the preferred MCP surface
- **THEN** the skill SHALL direct the agent to use `gh` as a fallback
- **AND** it SHALL disclose that fallback and the unavailable MCP data in its
  report

### Requirement: Git PR triage preserves reviewed-comment state
The skill SHALL use a repository-local state file at
`{{path.documents}}review-comments/<owner>-<repo>-pr-<number>.json` to distinguish
previously reported review comments from newly observed comments. It SHALL use
stable provider identifiers where available and a deterministic fallback key
otherwise, preserve concern fingerprints for repeat detection, and write state
only after reporting completes successfully.

#### Scenario: Previously reported comment is seen again
- **WHEN** a later triage run retrieves a comment whose stable key is already
  recorded
- **THEN** the skill SHALL exclude it from new findings
- **AND** it SHALL recognise a new identifier with the same concern fingerprint
  as a repeated concern rather than a new issue

#### Scenario: New review feedback is reported
- **WHEN** a triage run identifies new or repeated review feedback and produces
  its report
- **THEN** it SHALL record stable identity, source, location, timing,
  normalised summary, and concern fingerprint for that feedback
- **AND** a later run SHALL not re-examine it as a new concern

#### Scenario: Triage fails before a report
- **WHEN** review retrieval or analysis fails before a user-facing report is
  produced
- **THEN** the skill SHALL NOT mark any retrieved comment as seen

### Requirement: Git PR triage groups and recommends review actions
The skill SHALL collate all retrieved review feedback and combine comments
describing the same actionable concern while retaining reviewer, source, and
location references. It SHALL classify each group using one primary
classification, determine whether it is actionable, deferred, declined, or
stale, and recommend `fix`, `defer`, `decline`, `ask reviewer`, or `no action`
with a concise rationale.

#### Scenario: Duplicate review comments describe one defect
- **WHEN** multiple reviewers or comment threads describe the same underlying
  concern
- **THEN** the skill SHALL report one grouped finding
- **AND** it SHALL preserve all reviewers, links, and path or line references

#### Scenario: Current code makes a comment stale
- **WHEN** current pull-request context resolves or supersedes a review comment
- **THEN** the skill SHALL classify it as `stale_or_not_applicable`
- **AND** it SHALL explain the relevant current state and recommend no action

### Requirement: Git PR triage honours the user's presentation preference
After building a stable inventory of new grouped concerns, the skill SHALL
present a concise grouped report by default. When the user prefers a sequential
walkthrough instead of a grouped report, it SHALL recommend and direct the
agent to invoke `just-one` for that inventory. It SHALL not invoke `just-one`
without that preference.

#### Scenario: User accepts grouped reporting
- **WHEN** the user does not request sequential triage
- **THEN** the skill SHALL present grouped findings and recommendations
- **AND** it SHALL NOT invoke `just-one`

#### Scenario: User requests sequential triage
- **WHEN** the user prefers a one-at-a-time walkthrough of the inventory
- **THEN** the skill SHALL recommend `just-one`
- **AND** it SHALL direct the agent to use that skill without implementing any
  accepted action during the walkthrough
