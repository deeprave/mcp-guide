# Proposal

## Why

Pull-request review comments need a repeatable, durable triage path that
distinguishes newly raised concerns from comments already examined in earlier
runs. The existing `read-pr-reviews` skill defines that behaviour, but it is
not available as a bundled Guide skill and does not offer the user's preferred
sequential decision experience.

## What Changes

- Add a bundled `git-pr-triage` Guide skill that reads inline review threads,
  review summaries, and review-related issue comments for a selected pull
  request.
- Use an explicitly supplied pull request, an active contextual pull request,
  or the current branch before asking the user to identify one.
- Persist stable seen-comment and repeated-concern state through
  `{{path.documents}}` so later invocations report only newly actionable review
  feedback.
- Collate review concerns from all supported review surfaces, verify them
  against the current pull-request diff and source, combine duplicates,
  classify them, and recommend an action without making changes.
- Offer `just-one` triage only when the user prefers a sequential walkthrough
  instead of a grouped report; preserve the user's choice for the current
  triage session.

## Capabilities

### New Capabilities
- `git-pr-triage`: Pull-request review-comment discovery, durable novelty
  tracking, grouped analysis, and optional sequential decision triage.

### Modified Capabilities
- `git-skills`: Add `git-pr-triage` to the independently available bundled Git
  skill packages.

## Impact

- Bundled skill package templates, Guide skill discovery, and authoring
  documentation.
- GitHub review-comment retrieval and a repository-local durable state file
  beneath `{{path.documents}}review-comments/`.
- Behavioural tests for rendered skill guidance and persisted review-comment
  state; no pull-request changes are made by the triage skill itself.
