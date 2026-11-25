# Tasks

## 1. Public skill identities

- [x] 1.1 Move workflow skill packages from `_skills/workflow/<name>` to `_skills/guide/<name>` and rename their declared public names to `guide-*`; verify discovery resolves each new identity while the old identities do not resolve.
- [x] 1.2 Move Git skill packages from `_skills/git/<name>` to `_skills/guide/git/<name>` and rename their declared public names to `guide-git-*`; verify discovery resolves each new identity while the old identities do not resolve.
- [x] 1.3 Replace specialised triage packages with `_skills/guide/triage` and `_skills/guide/sequence`, exposing `guide-triage` and `guide-sequence`; verify discovery exposes only the new names.

## 2. Unified triage and sequential decisions

- [x] 2.1 Consolidate review-report and pull-request triage into `guide-triage`, and verify explicit input overrides context while applicable bound and unbound contexts select the correct evidence.
- [x] 2.2 Collate independent review reports, external feedback, and pull-request threads into the issue-specific `review-findings.json` record without modifying source evidence, and verify duplicate concerns retain their sources.
- [x] 2.3 Implement `guide-sequence` as an ordered conversational walkthrough with its review and non-review decision sets, and verify it records decisions without executing follow-up actions.

## 3. Guide-owned references

- [x] 3.1 Update template `skill` and `recommend` references targeting renamed or replaced skills, and verify their rendered URIs select the new public identities.
- [x] 3.2 Update built-in command, skill, and help references that select renamed skills without changing command identifiers or command-template locations, and verify the affected command and skill entrypoints retain their existing behaviour.
- [x] 3.3 Add approachable user skills documentation and index it, update developer skill authoring guidance, search all other documentation for renamed-skill references, and include the v2.1.0 breaking-change entry; verify documented names and package locations match the catalogue.

## 4. Behavioural coverage and specifications

- [x] 4.1 Update behavioural coverage for renamed and consolidated built-in skill identities, and verify catalogue, `guide://$`, `skill://`, and `use_skill` resolution use the new names.
- [x] 4.2 Sync the approved Guide skill, package-hierarchy, and recommendation specification deltas after implementation, and verify the main specifications describe the renamed identities.
