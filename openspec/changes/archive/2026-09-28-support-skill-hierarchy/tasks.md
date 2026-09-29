## 1. Package identity and discovery

- [x] 1.1 Define and validate the required unique public `name` in skill entrypoint frontmatter, and verify missing, blank, invalid, and duplicate names leave packages unavailable with diagnostics
- [x] 1.2 Extend runtime-owned, mutex-coordinated discovery to find nested `SKILL.md` package roots, build a public-name dictionary containing each package root relative to `_skills` and its `requires-*` declarations, refresh on effective recursive skills-tree mtime changes, and bypass cache reuse in guide-development mode
- [x] 1.3 Move bundled `git-*` and `workflow-*` packages into matching nested directories with declared names, and verify their existing public names remain available

## 2. Resolution and catalogue

- [x] 2.1 Resolve entrypoints and members from the public name-to-package mapping while retaining literal-member containment checks, and verify a nested package responds to its flat `guide://$<name>` URI
- [x] 2.2 Keep catalogue, list_skills, prompt, and native resource results keyed by the declared public name; evaluate `requires-<flag>` against the requesting session before advertisement or resolution; and verify returned file messages use virtual `<skill-name>/<member>` paths without exposing server-side directories
- [x] 2.3 Preserve flat-package compatibility and verify existing skill resource and prompt calls retain their public URIs

## 3. Implementation tests and documentation

- [x] 3.1 Add focused tests for nested discovery, duplicate-name rejection, runtime cache refresh and guide-development bypass, per-session `requires-<flag>` availability from the shared mapping, nested member retrieval, virtual public paths, bundled-package relocation, and unchanged flat-package retrieval, and verify the targeted pytest suite passes
- [x] 3.2 Update skill authoring documentation with public-name and hierarchy rules, and verify documented examples match the resource contract

## 4. Triage category and reusable item decisions

- [x] 4.1 Move and rename `just-one` to `_skills/triage/items/` with public name `triage-items`; generalise its directives for any stable inventory, context-derived selection, optional `Triage/<derived-key>.json` decision ledgers, and explicitly authorised follow-up actions
- [x] 4.2 Move and rename `git-pr-triage` to `_skills/triage/pr/` with public name `triage-pr`; define its pull-request-author response and conversation-resolution boundary, and recommend `triage-items` for serial decisions
- [x] 4.3 Move and rename `workflow-triage` to `_skills/triage/review/` with public name `triage-review`; preserve workflow issue collation, include every valid source on initial collation, and use the canonical-inventory cutoff for incremental re-triage unless the user requests historical re-collation
- [x] 4.4 Remove handoff-context directives from every bundled skill, and update bundled recommendations, documentation, and current OpenSpec specifications to use the three renamed identities
- [x] 4.5 Add behavioural coverage for renamed-skill discovery, retired-name absence, generic non-workflow inventories, durable `Triage/` ledgers, all-source workflow collation guidance, and explicit-authority guardrails
- [x] 4.6 Require workflow-review source records to use only the producing reviewer's own `<agent-name>-<model-name>` identity, prohibit adopted identities and `-heavy`/`-light` suffixes, and update the source-record format and OpenSpec contract without a static template-content test
- [x] 4.7 Align `triage-review` source references with `<agent-name>-<model-name>` identities, present only pending and newly collated findings during incremental triage, allow `triage-pr` grouped or serial presentation according to user preference, and restore compact `triage-items` priority and Target/Scope presentation

## 5. Discovery cache refinement

- [x] 5.1 Keep the public name only as the discovery-map key; cache complete frontmatter without `name` and an immutable `requires-*` mapping for session visibility checks, and select a skill by direct flat-name lookup before resolving its contained member path
- [x] 5.2 Preserve the last valid discovery mapping on validation or refresh failure, and add a five-minute non-development cache-age fast path that returns the mapping without filesystem I/O or timestamp changes
- [x] 5.3 Add behavioural tests for public resource resolution, direct flat-name member selection, cached visibility requirements, cache-age reuse, failed-refresh retention, and the updated triage guidance; run targeted and full pytest suites

## 6. Review-target elicitation remediation

- [x] 6.1 Restore `main` as a review-target choice and render selected branch and pull-request values in workflow-review instructions.
- [x] 6.2 Honour modern cancelled `fallback: render` forms and re-evaluate conditional forms after each legacy elicitation response, with behaviour-focused unit coverage.
