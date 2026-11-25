# Tasks

## 1. Public skill identities

- [ ] 1.1 Rename the declared public names of the selected workflow packages to `guide-*`, and verify skill discovery advertises and resolves each new identity while the old identities do not resolve.
- [ ] 1.2 Rename the declared public names of the selected Git packages to `guide-git-*`, and verify skill discovery advertises and resolves each new identity while the old identities do not resolve.
- [ ] 1.3 Replace the specialised triage public identities with `guide-triage` and `guide-sequence`, and verify discovery exposes only the new names.

## 2. Unified triage and sequential decisions

- [ ] 2.1 Consolidate review-report and pull-request triage into `guide-triage`, and verify explicit input overrides context while applicable bound and unbound contexts select the correct evidence.
- [ ] 2.2 Collate independent review reports, external feedback, and pull-request threads into the issue-specific `review-findings.json` record without modifying source evidence, and verify duplicate concerns retain their sources.
- [ ] 2.3 Implement `guide-sequence` as an ordered conversational walkthrough with its review and non-review decision sets, and verify it records decisions without executing follow-up actions.

## 3. Guide-owned references

- [ ] 3.1 Update template `skill` and `recommend` references targeting renamed or replaced skills, and verify their rendered URIs select the new public identities.
- [ ] 3.2 Update built-in command, skill, and help references that select renamed skills without changing command identifiers, and verify the affected command and skill entrypoints retain their existing behaviour.
- [ ] 3.3 Update user and developer documentation naming the selected built-in skills, including the v2.1.0 changelog's breaking-change entry, and verify the documented names match the catalogue identities.

## 4. Behavioural coverage and specifications

- [ ] 4.1 Update behavioural coverage for renamed and consolidated built-in skill identities, and verify catalogue, `guide://$`, `skill://`, and `use_skill` resolution use the new names.
- [ ] 4.2 Sync the approved Guide skill, package-hierarchy, and recommendation specification deltas after implementation, and verify the main specifications describe the renamed identities.
