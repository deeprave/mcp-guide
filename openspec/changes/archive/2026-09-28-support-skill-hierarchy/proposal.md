## Why

Guide skills are currently stored and discovered as flat packages. That keeps
the first implementation portable, but it prevents the server-owned skill tree
from being organised by subject without changing public skill identifiers or
resource URIs.

## What Changes

- Permit nested skill packages below the private `_skills` directory
- Require every discovered package to declare one globally unique, flat public
  skill name in its frontmatter
- Advertise and resolve skills only by that public name, regardless of the
  package's directory hierarchy
- Keep the discovered public-name-to-package-directory mapping on GuideRuntime,
  refresh it under runtime mutex-style coordination when the effective
  recursive skills-tree mtime changes, and bypass cache reuse in
  guide-development mode
- Preserve session-specific `requires-<flag>` availability when advertising or
  resolving packages from the shared runtime mapping
- Reorganise bundled `git-*` and `workflow-*` skills into matching nested
  packages without changing their public names or URIs
- Introduce a `triage` skill category with public `triage-items`, `triage-pr`,
  and `triage-review` identities. Retire the awkward, narrower `just-one`,
  `git-pr-triage`, and `workflow-triage` identities.
- Make item triage reusable for a stable inventory from context or an explicit
  user selection, with an optional durable decision ledger under
  `{{path.documents}}Triage/` when no existing canonical record applies.
- Remove handoff-context directives from every bundled skill; handover is a
  user preference, not a skill responsibility.
- Require workflow-review source records to use each reviewer's own
  agent-and-model identity, rather than review-role suffixes or identities
  found in other review records.
- Preserve the existing flat package layout and public skill URI behaviour
  except for the three deliberately renamed triage skills.

## Capabilities

### New Capabilities

- `skill-package-hierarchy`: Discover hierarchical server-side skill packages
  while exposing stable, flat, unique public skill names

### Modified Capabilities

- `guide-url-skills`: Rename the item and workflow-triage skill contracts and
  require reviewer-owned agent-and-model source-record filenames.
- `git-skills`: Replace the retired `git-pr-triage` package identity with
  `triage-pr`.

## Impact

- Skill discovery, catalogue construction, URI resolution, and package-member
  retrieval
- Skill authoring documentation and validation
- Existing flat packaged skills, which remain supported without renaming
- The three intentionally retired triage identifiers and all recommendations
  that refer to them
