## Context

See proposal.md - Why. This change is documentation-only. Relevant facts from this session's code reading:

- `TemplateContextCache.get_template_contexts()` (`src/mcp_guide/render/cache.py`) layers context as `project → agent → client → system`, plus a separately-merged `openspec` layer that is never cached (rebuilt fresh per render, per its own docstring, due to lazy TTL/mtime-observed validity). Each layer's variables are built by a dedicated `_build_*_context` method:
  - `_build_system_context`: `server.*`, and several `INSTRUCTION_*` constants exposed as raw template variables (static, always present).
  - `_build_client_context`: `client.*`, `user`, `repo` — sourced from `TaskManager` cached data (`client_os_info`, `client_context_info`); empty `{"client": {}}` if no task manager (i.e. no session).
  - `_build_agent_context`: `@`, `tool_prefix` (process-global env var, always present even with no session), `agent.*` (only if `session.agent_info` is set), styling/formatting variables, `tasks` (task statistics, only if a task manager exists).
  - `_build_project_context`: `project.*`, `client_working_dir`, `path.*`, `flags`/`flag_values`, `feature_flags`/`feature_flag_values`, `projects`/`projects_count`, `workflow-file`, and a `workflow.*` child layer if workflow is enabled for the bound project — all degrade to empty defaults with no bound project (confirmed this session: `session=None` renders this layer as empty rather than raising).
  - `_build_openspec_context`: `openspec.*` (available, version, changes, show, status, has_version lambda) if an `OpenSpecTask` subscriber exists on the session's task manager; otherwise `{"openspec": False}`.
  - `get_transient_context()`: `timestamp`/`timestamp_ms`/`timestamp_ns`, `now.*`, `now_utc.*` — always available, generated fresh per call, not part of the cached layered context.
- Category-specific and command-specific extra context: policy pre-rendering injects `policy_topic`, `policy_category`, `policy_path` per pre-rendered document (per `template-rendering`'s existing OpenSpec requirement "Policy Partial Context Variables"); `_build_category_context` injects `category.*` when a category name is given to `get_template_contexts`. Individual command templates may receive further `extra_context` from their calling code (e.g. the `_filesystem-probe` template's `path` variable, the `_project-root` template's `tool_prefix` usage inherited from the agent layer). A complete reference needs to enumerate both the layered/always-available variables and this per-template/per-command injection pattern, since the two are easy to conflate.
- `cooperative-result-disposition` (separate, in-progress change) introduces `disposition` as a `Result` field distinct from template frontmatter `type:`, plus a new `_system/_disposition-guide.mustache` template. Documenting these depends on that change actually landing first for the specifics (exact vocabulary wording, exact template content) to document accurately, even though the general shape (a `Result.disposition` field exists, is distinct from frontmatter `type:`) is already true today and can be documented independent of that change's completion.

## Goals / Non-Goals

**Goals:**
- Produce one authoritative, complete template-variable reference covering every layer and both the bound and unbound session cases.
- Document `Result.disposition` as distinct from frontmatter `type:`, and their relationship.
- Document the document/command/skill/resource relationship at a level that answers "how do these four things relate" without requiring a source-code read.
- Preserve the existing cross-reference structure between developer docs files rather than duplicating content.

**Non-Goals:**
- Documenting the disposition vocabulary's exact final wording before `cooperative-result-disposition` lands — that part of this change is sequenced after, not concurrent with, that change's implementation.
- Changing any source code, spec, or observable behavior (this is `skip_specs: true`).
- Auditing or correcting existing developer docs for accuracy issues unrelated to this change's scope (that overlaps with `update-openspec-specs`'s spirit but for `docs/`, not `openspec/specs/`; not addressed here).

## Decisions

### New file for the template variable reference, not folded into template-rendering.md

**Decision:** Create a new `docs/developer/template-variables.md` (or similarly named) file dedicated to the complete variable reference, cross-referenced from `template-rendering.md` rather than appended to it.

**Why:** `template-rendering.md` is already a general "how templates work" guide; a complete per-layer variable enumeration (every field in `_build_system_context` through `_build_openspec_context`, bound vs. unbound behavior for each) is reference material of a different kind and length than the rest of that file — mixing them risks making both harder to navigate. This mirrors the existing pattern where `skill-authoring.md` cross-references rather than duplicates frontmatter documentation.

**Alternatives considered:** Append to `template-rendering.md` directly — rejected; that file would grow substantially and mix "how to write a template" with "here is every variable," two different reader intents.

### Sequence disposition documentation after cooperative-result-disposition lands

**Decision:** Document the general existence and purpose of `Result.disposition` (as distinct from frontmatter `type:`) now, since that's already true of the current code, but defer documenting the specific vocabulary (`agent/error`, `user/error`, the disposition-guide template's exact content) until `cooperative-result-disposition` has actually implemented them.

**Why:** Documenting a vocabulary and teaching mechanism that doesn't exist yet risks the docs becoming inaccurate the moment that change's implementation differs even slightly from its current proposal/design (which is plan, not shipped code). Documenting only what's real today, with an explicit forward-reference for what's coming, avoids that risk.

**Alternatives considered:** Document the full planned vocabulary now, sourced from `cooperative-result-disposition`'s proposal/design — rejected; those are planning artifacts, not confirmed shipped behavior, and this change explicitly documents current behavior.

## Risks / Trade-offs

- **[Risk]** Publishing an incomplete disposition section (general concept only, vocabulary deferred) could read as unfinished to a contributor discovering it before the follow-up lands. → **Mitigation:** state explicitly in the doc that the full vocabulary is landing separately, with a pointer to the `cooperative-result-disposition` change, rather than leaving an unexplained gap.
- **[Risk]** The variable reference could drift out of sync with `render/cache.py` if that file changes after this documentation ships, since nothing enforces the two staying aligned. → **Mitigation:** out of scope to solve mechanically in this change; noting the risk here so a future contributor updating `_build_*_context` knows to check this doc, is the practical mitigation available without new tooling.

## Migration Plan

No migration — documentation-only, additive. No rollback complexity beyond normal doc edits.
