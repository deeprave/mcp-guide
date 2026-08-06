## Context

Profiles compose categories and collections into a project configuration. The default profile has a review category whose pattern does not select its general guidance and lacks a code-review collection; Docker and shell projects have no corresponding profile content.

## Goals / Non-Goals

**Goals:**
- Make default review guidance and code-review collection usable.
- Make baseline check guidance usable.
- Add Docker and shell language guidance through normal profile selection.
- Reject invalid empty profile collections.
- Ensure static bundled resource references identify real, renderable content or commands in the configuration that enables them.

**Non-Goals:**
- Detecting languages automatically or changing existing project configurations retroactively.
- Require every resource to resolve in an unconfigured default project. Some resources intentionally require onboarding choices or an enabled profile.

## Decisions

- Represent Docker and shell support as profiles and templates, matching existing language content conventions.
- Treat Docker guidance as `lang/docker` rather than choosing a host-language-specific location; Dockerfiles are independent of the image's implementation language.
- Validate collection membership during profile load, before any project mutation.
- Treat literal `{{#resource}}...{{/resource}}` targets as bundled-content contracts. A target may depend on a profile or feature, but must exist and produce non-empty rendered output whenever that feature is enabled. Dynamic targets (for example, a user-configured startup-instruction value) remain runtime-configurable and are outside the static audit.

## Risks / Trade-offs

- [Existing malformed profile files fail to load] → audit bundled profiles and provide clear validation errors.
- [Shell dialect differences] → document shared Bash/Zsh practices and identify dialect-sensitive syntax.
- [Optional resources are incorrectly required by a fresh default project] → validate each static reference in the configuration that owns it, rather than requiring universal default resolution.
