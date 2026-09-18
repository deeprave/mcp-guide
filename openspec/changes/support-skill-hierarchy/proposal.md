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
- Preserve the existing flat package layout and public skill URI behaviour

## Capabilities

### New Capabilities

- `skill-package-hierarchy`: Discover hierarchical server-side skill packages
  while exposing stable, flat, unique public skill names

### Modified Capabilities

- None

## Impact

- Skill discovery, catalogue construction, URI resolution, and package-member
  retrieval
- Skill authoring documentation and validation
- Existing flat packaged skills, which remain supported without renaming
