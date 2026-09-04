# ADR-013: Portable Configuration Path Values

**Status:** Accepted
**Date:** 2026-09-03
**Related change:** `use-request-context`

## Context

Guide persists process configuration in `config.yaml`, including `docroot`.
The same file is copied between hosts, worktrees, and Docker images. Reviewers
have repeatedly proposed calling `.resolve()` or `.absolute()` on a
user-supplied `--docroot` or `docroot:` value before it is written, so later
use cannot depend on the process working directory.

That conversion replaces a user-anchored location with a host-specific
filesystem path. A file that said `docroot: docs` would become
`/Users/someone/project/docs` on the writing machine and would be wrong after
the config is copied elsewhere.

From the user's point of view, `docs` is already an absolute location: it is
the document root they named, anchored in their environment. It is not an
incomplete path waiting for Guide to finish it.

A separate rule already covers the case where the user did not supply a
docroot: a missing or blank key is filled with a host-absolute default beside
the configuration file, so Guide never invents a CWD-anchored default. That is
not a user-authored path.

## Decision

User-supplied path values in the configuration file remain as the user wrote
them.

- A user-anchored `docroot` from `--docroot`, `MG_DOCROOT`, or `docroot:` is
  persisted as written and later used as the resolver base without rewriting.
- Do not call `.resolve()` or `.absolute()` on a user-supplied path in order
  to "fix" it before writing `config.yaml`.
- `~` and environment variables such as `$HOME` may be expanded at use time;
  that does not authorise converting a user-anchored path into a host-absolute one.
- When the user did not supply a docroot, keep the existing missing-key
  default: persist a host-absolute path beside the configuration file, and do
  not invent a CWD-anchored default.

Document-path joins remain lexical through the request-context resolver. That
helper maps a document path onto the configured root; it does not rewrite the
configured root itself.

## Consequences

- The same `config.yaml` can be copied to another system or container and
  still name the intended tree in that environment.
- A user-anchored `docroot` is the location the user specified. When the
  process needs a filesystem path, it interprets that value in its own
  environment. That is accepted. Operators who want a host-fixed location
  write a host-absolute path.
- Filling a missing `docroot` key remains a host-absolute, config-adjacent
  default and is not a portable user value.
