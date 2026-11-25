# Proposal

## Why

Guide's server-owned skills share generic public names with skills a user may
already have installed. Namespacing the selective internal operational skills
makes their origin clear and prevents ambiguous recommendations, catalogue
entries, and resource URIs.

## What Changes

- **BREAKING** Rename the selected server-owned `workflow-*` skills to their
  corresponding `guide-*` names.
- **BREAKING** Rename every server-owned `git-*` skill to `guide-git-*`.
- Reorganise the renamed and consolidated packages beneath `_skills/guide`
  while retaining all Guide command URIs and command-template locations.
- **BREAKING** Replace `triage-review` and `triage-pr` with one contextual
  `guide-triage` skill, and replace `triage-items` with `guide-sequence`.
- Collate review reports, external reviews, and pull-request feedback into one
  issue-specific cache record while retaining independent source evidence.
- Make sequential presentation and its review/non-review decisions
  conversational so exported skills remain usable without Guide runtime support.
- Update internal skill recommendations, resource examples, documentation, and
  behavioural coverage to use the renamed public identities.
- Preserve each skill's availability, rendering, elicitation, and command
  pairing behaviour.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-url-skills`: Expose the renamed Guide operational skills and the
  unified triage and sequential-presentation behaviours.
- `skill-package-hierarchy`: Declare the renamed public identities for the
  existing workflow and Git packages while retaining their package locations.
- `recommend-items`: Render recommendations for renamed Guide Git skills.

## Impact

- Built-in skill frontmatter and package hierarchy, review-cache records,
  command-to-skill references, user and developer documentation, and all
  internal references to the renamed skills.
- Guide skill discovery, `guide://$`, `skill://`, `use_skill`, documentation,
  and tests that name those public skills.
- User-installed skills remain unchanged.
