## Context

Profiles compose categories and collections into a project configuration. The default profile has a review category whose pattern does not select its general guidance and lacks a code-review collection; Docker and shell projects have no corresponding profile content.

## Goals / Non-Goals

**Goals:**
- Make default review guidance and code-review collection usable.
- Add Docker and shell language guidance through normal profile selection.
- Reject invalid empty profile collections.

**Non-Goals:**
- Detecting languages automatically or changing existing project configurations retroactively.

## Decisions

- Represent Docker and shell support as profiles and templates, matching existing language content conventions.
- Treat Docker guidance as `lang/docker` rather than choosing a host-language-specific location; Dockerfiles are independent of the image's implementation language.
- Validate collection membership during profile load, before any project mutation.

## Risks / Trade-offs

- [Existing malformed profile files fail to load] → audit bundled profiles and provide clear validation errors.
- [Shell dialect differences] → document shared Bash/Zsh practices and identify dialect-sensitive syntax.
