# Design

## Context

Guide discovers the package directories under `_skills` and exposes the
frontmatter `name` as the public identity used by the skill catalogue,
`guide://$`, `skill://`, `use_skill`, and template references. The private
directory hierarchy is deliberately independent of that identity.

## Goals / Non-Goals

**Goals:**

- Give the selected Guide-owned operational skills unambiguous public names.
- Reorganise selected package paths while preserving rendering, eligibility,
  elicitation, and paired command behaviour.
- Consolidate review and pull-request triage around their shared evidence and
  decision model.
- Keep serial decisions usable by exported skills without Guide runtime state.

**Non-Goals:**

- Renaming commands, command-template locations, user-installed skills, or
  arbitrary skills whose names happen to share the same prefixes.
- Providing compatibility aliases for the replaced public skill names.

## Decisions

### Rename frontmatter identities and consolidate package locations

The following existing packages will move and receive new public frontmatter
names:

| Existing package | New package | Public name |
| --- | --- | --- |
| `_skills/workflow/<name>` | `_skills/guide/<name>` | `guide-<name>` |
| `_skills/git/<name>` | `_skills/guide/git/<name>` | `guide-git-<name>` |
| `_skills/triage/{pr,review}` | `_skills/guide/triage` | `guide-triage` |
| `_skills/triage/items` | `_skills/guide/sequence` | `guide-sequence` |

Discovery already uses the frontmatter identity rather than the directory
path, so this preserves the shared resolver and avoids a skill-specific
compatibility path. The former names intentionally cease to resolve,
preventing renewed ambiguity with a user's installed skills.

### Consolidate triage and serial presentation

`guide-triage` chooses its input from explicit review material first, then
the active workflow issue or pull request. It collates independent agent
reports, external review records, and pull-request threads into a canonical
issue record at `{{path.cache}}reviews/{{project.hash}}/<issue>.json`.
The record preserves each source reference and its associated evidence;
deduplication combines concerns, not source records. An unbound pull-request
triage retains its provider/repository/pull-request cache record until an
issue-specific record is available. A pull request contributes to the local
issue record only when its head branch matches the current local branch;
otherwise it is triaged independently of the active workflow issue.

`guide-sequence` accepts a stable inventory from `guide-triage` or explicit
user material. Before presentation, it uses the user-selected ordering. It
presents only one item at a time with the sequence count, title, description,
and applicable optional priority, analysis, and recommendation fields. Review
inventories accept conversational Accept, Decline, Next, Skip, Vary, and
Defer decisions. Other inventories accept Ok or an Action supplied by the
user. Accept and Vary record follow-up but do not execute it; Defer records a
context todo.

This is intentionally conversational rather than a frontmatter elicitation:
such forms only run while a skill is resolved and cannot drive a per-item
loop. The rendered skill therefore remains useful after export without Guide
runtime state or MCP elicitation support.

### Update only references to renamed Guide skills

Template `skill` and `recommend` values, help text, documentation, and
behavioural coverage that name a selected built-in skill will use its new
public identity. Generic fixtures and examples that test public-name mechanics
rather than a bundled Guide skill need not be renamed.

### Keep commands independent

The existing `guide://_workflow/...` and related command URIs are commands,
not skills. Their names and filesystem locations remain stable; only references
that select a renamed skill change.

### Document the public skills surface

Add `docs/user/skills.md` in the same approachable style as the existing user
guides and link it from the documentation index. Update the existing developer
authoring guide for the new hierarchy, then search the remaining documentation
and templates for renamed public skill references.

## Risks / Trade-offs

- [Existing client references break] → The proposal explicitly marks this as a
  breaking public-identity change and updates Guide-owned discovery and
  reference surfaces together.
- [An outdated internal reference points to a removed name] → Search the
  templates, documentation, and targeted behavioural coverage for every old
  selected built-in identity.
- [Exported serial handling lacks Guide state] → Keep its decision loop
  conversational and require explicit material when no applicable context is
  available.
