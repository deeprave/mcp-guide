## Context

See [proposal.md](proposal.md) for the motivation. The shared profile loader forms
`<profiles directory>/<caller name>.yaml`, checks it, and reads it directly. Its
callers include profile application, profile inspection, category-filtered profile
listing, and default-profile initialisation. Validation only at a tool boundary
would leave internal callers and future entry points unprotected.

## Goals / Non-Goals

**Goals:**

- Make profile identifiers unambiguously filename basenames.
- Ensure the file actually read is canonically contained by the bundled profiles
  directory, including after symlink resolution.
- Preserve normal profile application, inspection, discovery, and `_default`
  initialisation behaviour.

**Non-Goals:**

- Allowing profile directories, file extensions, aliases, or user-defined profile
  locations.
- Changing YAML schema validation, profile composition, or template resource paths.
- Hardening unrelated filesystem reads.

## Decisions

### Validate identifiers centrally before path construction

Add one shared profile-identifier validator used by the profile loader before
constructing a candidate path or checking its existence. Valid identifiers are
one to 50 Unicode alphanumeric, underscore, or hyphen characters. This preserves
the existing built-in `_default` profile while excluding slashes, backslashes,
periods, whitespace, suffixes, and absolute-path forms.

Central validation is chosen over separate Pydantic field validators on the
`use_project_profile` and `show_profile` tool arguments because direct model calls,
filtered listing, and default configuration loading all use the same loader.

Alternative considered: reject only `..`. Rejected because separators, absolute
paths, suffix tricks, and platform-specific path spellings still make the input
something other than a profile basename.

### Canonical containment immediately before reading

Resolve the profiles directory to its canonical path, construct the `.yaml`
candidate only from a valid basename, resolve that candidate, and require its final
canonical target to be relative to the canonical profiles directory immediately
before opening it. This permits a symlink used within the packaged profiles
directory but rejects an outward symlink even though its lexical path begins in the
directory.

The loader will treat a containment failure as a safe validation error and avoid
including the candidate's external canonical path in user-visible text. A missing
contained candidate remains `FileNotFoundError` so existing tool mappings retain
their not-found behaviour.

Alternative considered: rely on a validated basename alone. Rejected because a
valid `name.yaml` entry can itself be a symlink outside the profiles directory.
Alternative considered: use only lexical `relative_to` checks. Rejected because it
does not verify a symlink's final target.

## Risks / Trade-offs

- [An existing external symlink was intentionally used as a profile] → It is now
  rejected because profile content is constrained to the trusted profiles root.
- [Unicode identifier rules differ between platforms] → Validate strings before
  filesystem access and retain the project's existing Unicode name convention.
- [A profile changes between canonical check and read] → Perform the containment
  check immediately before the read and keep the profile root packaged/read-only
  in normal deployment; add a regression test for the check/read boundary.
- [Callers depend on detailed missing-path text] → Preserve not-found semantics
  for valid contained names while reducing external-target detail for invalid input.

## Migration Plan

1. Add the shared basename validator and canonical containment helper to the
   profile model, with unit coverage for accepted and rejected identifiers.
2. Route every `Profile.load` read through the helper and preserve the existing
   not-found versus invalid-name mappings in project tools and configuration.
3. Add symlink escape and contained-symlink regression tests, then run profile
   model and profile-application integration tests.

No data migration is required. Rollback restores the former profile-loading
behaviour, but deployments should not rely on profiles outside the packaged root.
