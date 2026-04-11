# Design: add-category-topics

## Context

The `policies` category contains 71 documents organized into topic sub-paths
(e.g. `policies/git/ops/`, `policies/testing/`). Users activate policies by configuring
glob patterns on the `policies` category in their project settings. The system must:

1. Resolve which documents are active for a given topic sub-path
2. Deliver those documents to templates (via mustache partials) and to guide resources (via URI)
3. Handle the case where no policy is selected for a topic gracefully

This design is constrained by the existing partial machinery (`{{> key}}`), the existing
`get_category_content` / `internal_get_category_content` delegation chain, and the need to
keep stored project documents (not just filesystem templates) as valid policy sources.

## Goals / Non-Goals

**Goals:**
- Discovery function that queries both filesystem templates and stored documents uniformly
- Sub-path filtering that narrows existing project patterns without overriding them
- Policy pre-rendering that reuses the partial machinery's code path
- Clear informational placeholder for unselected policy topics
- Composable resolution (all matching documents concatenated)

**Non-Goals:**
- Tracking whether topics are exclusive (mutually exclusive selection is user's responsibility)
- A new policy object model (policies are plain documents in a category)
- Guided onboarding or automatic policy detection (belongs to `add-guided-onboarding`)
- Implementing every possible policy topic in one pass

## Decisions

### D1: Pre-rendering vs lazy rendering for policy partials

**Decision:** Pre-render all declared policy topics before the main template renders.

**Why:** Each matched document needs its own `policy_topic`, `policy_category`, and `policy_path`
context variables at render time. Lazy rendering (resolving `{{> git/ops}}` at the point of use)
would have access only to the parent template's context. Pre-rendering allows setting per-document
context before mustache processes the parent template.

**Alternative considered:** A custom mustache lambda per topic that renders lazily. Rejected:
mustache lambdas are complex, harder to test, and would require exposing implementation details
to the template layer.

### D2: Trailing slash as the sub-path filter signal

**Decision:** A trailing slash in the document pattern (e.g. `"git/ops/"`) is the primary signal
that sub-path filtering is requested, not exact-document matching.

**Why:** It is unambiguous — a path that ends with `/` cannot be a document name. It is also
familiar from Unix conventions (directory vs file). The internal implementation can append a
trailing slash when constructing topic-derived filter patterns.

**Alternative considered:** A separate boolean parameter `sub_path=True`. Rejected: would require
API changes throughout the delegation chain.

### D3: Prefix-filter semantics (not override)

**Decision:** Sub-path filtering narrows the documents matched by the project's existing configured
patterns. It does not replace them.

**Why:** Users configure which policy variant they want via patterns (e.g. `git/ops/conservative*`).
If sub-path filtering overrode those patterns, a `guide://policies/git/ops` request would return
all documents under `git/ops/` regardless of the user's selection — defeating the purpose of
pattern-based policy selection.

**Example:**
- Configured pattern: `git/ops/conservative*`
- Sub-path filter: `git/ops/`
- Result: documents matching `git/ops/conservative*` that are also under `git/ops/`

### D4: `discover_category_documents` as the shared lower level

**Decision:** Introduce `discover_category_documents(category, pattern)` as the shared function
used by both partial resolution and policy pre-rendering.

**Why:** The existing partial machinery queries only the filesystem template corpus. Policy
documents may also live as stored project documents. Extracting a shared function ensures both
code paths handle stored documents and filesystem templates uniformly.

**What it does NOT do:** It does not render content. It returns document paths/identifiers so that
the calling code (partial resolver or policy pre-renderer) can apply appropriate rendering context.

### D5: Frontmatter from policy documents is merged, not stripped

**Decision:** Frontmatter from policy documents is processed the same way as frontmatter from
regular partials: fields are combined and deduplicated, not stripped.

**Why:** Policy documents carry `type: agent/instruction` and `description:` fields that have
semantic meaning for the rendering pipeline (instruction resolution, type-based defaults). Stripping
would lose that metadata.

### D6: Resolver concatenates all matches (composable by default)

**Decision:** The policy resolver concatenates all documents matching the active patterns for a
topic. It does not enforce exclusivity.

**Why:** The resolver cannot know which topics are designed to be mutually exclusive and which are
composable. That knowledge belongs to the user (who selects patterns) and the policy corpus
documentation (`_INDEX.md`). Enforcing exclusivity at the resolver level would be wrong for
composable topics like `tooling/general/`.

### D7: `INSTRUCTION_MISSING_POLICY` is informational, not mandatory

**Decision:** When a template declares a policy topic that has no active selection, the rendered
placeholder instructs the AI that no policy is in effect for that topic. The AI should proceed
without enforcing any specific policy preference for that topic.

**Why:** A hard error would break templates when users haven't yet configured policies. The
placeholder makes the gap explicit without blocking the template from rendering.

## `_` Prefix Exclusion

Files and directories with a `_` prefix (e.g. `_INDEX.md`, `_missing_policy.md`) are excluded
from pattern matching in `discover_category_documents`. This mirrors the existing convention for
system files that should not be user-selectable.

## Risks / Trade-offs

- **Partial machinery refactoring** may introduce regressions in existing partial rendering.
  Mitigation: existing partial tests must all pass before and after the refactor.
- **Pre-rendering order** — policy topics are pre-rendered before the main template. If a policy
  document's frontmatter changes the rendering context in unexpected ways, it could affect the
  parent template. Mitigation: policy frontmatter is merged using the same rules as regular
  partials, which are already well-tested.
- **Performance** — pre-rendering all declared policy topics adds rendering overhead.
  Mitigation: policy includes are expected to be a small list; lazy loading is not worth the
  implementation complexity for this use case.

## Open Questions

- Should `guide://policies` (no topic) return a listing of all available topics?
- Should the `_missing_policy` template be per-language or a single system-wide template?
