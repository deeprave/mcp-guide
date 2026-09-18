## Context

The current skills implementation discovers only direct `_skills/*/SKILL.md`
packages and uses the directory name as the public identity. That makes public
names portable but prevents server-side organisation by subject. See
`proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**

- Separate server-side package location from the stable name exposed to agents
- Support nested packages without changing the public Guide skill URI shape
- Preserve existing flat package behaviour

**Non-Goals:**

- Nested public skill identifiers or public URI paths
- Changes to the standard local `SKILL.md` package format
- Automatic migration of third-party package trees

## Decisions

### Use entrypoint frontmatter as the public identity

Discovery will recursively locate renderable `SKILL.md` package roots. It will
parse each entrypoint's frontmatter and use its required `name` as the unique
public identifier. This lets `_skills/workflow/review/` expose
`workflow-review` and keeps the catalogue, tool, and URI surface flat.

The alternative, deriving a public identifier from nested directories, would
make package reorganisation a client-visible breaking change and reintroduce
slash-delimited skill identifiers that standard local skill catalogues do not
normally use.

### Resolve members through the discovered package record

The catalogue will retain a record mapping each public name to its validated
package root. Selection will first resolve that name, then resolve any member
path relative to the mapped root using the existing literal-member validation.
Directory structure will not be inferred from the requested URI.

### Treat invalid declarations as unavailable packages

An absent, blank, invalid, or duplicate public name makes a package
unavailable. Discovery logs a diagnostic identifying the affected package but
continues serving independent valid packages. This prevents arbitrary or
ambiguous resource routing.

## Risks / Trade-offs

- [A duplicate name hides a skill unexpectedly] → Log the conflicting paths
  and omit both packages until an author selects unique names
- [Recursive discovery expands scan work] → Reuse the existing mtime-aware
  discovery cache and limit traversal to the private skills root
- [A package is moved] → Its public name and URI remain unchanged, so only
  server-side source references need updating

## Migration Plan

1. Require a `name` for newly discovered package roots
2. Add `name` frontmatter to bundled flat packages before enabling recursive
   discovery
3. Validate discovery, duplicate handling, nested retrieval, and unchanged
   flat-package retrieval
4. Roll back by restoring flat-only discovery; bundled names are harmless
   metadata in that state
