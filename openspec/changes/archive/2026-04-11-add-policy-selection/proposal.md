# Change: Add Policy Selection

## Why

Many user-facing documents and templates currently mix:

- durable guidance that should apply broadly
- optional operational preferences that reflect one developer's choices

That makes the system harder to adapt to a user's actual preferences.

Examples include choices around:

- source control behavior
- whether AI should commit or open pull requests
- workflow strictness
- tooling preferences
- testing and type-checking posture
- autonomy and review expectations

Some of those choices are already separable through categories and collections, but many are still embedded directly in the default document set. Users installing the MCP are unlikely to know:

- what choices exist
- where they are encoded
- how to compose the available documents into a prompt that matches their own preferences

This change addresses the policy side of that problem by extracting optional choices into a dedicated `policy` category and making selected policies composable through the existing category, collection, profile, and guide resource mechanisms.

Guided onboarding is intentionally handled as a separate follow-on change. This change defines the policy material that onboarding will eventually help users choose.

## What Changes

### 1. Add a default `policy` category

Add `policy` to the default profile as a first-class category for optional steering documents.

Policy documents are plain markdown or templates and are organized by topic, for example:

- `policy/git/allow-commit`
- `policy/git/disallow-commit`
- `policy/workflow/full-phases`
- `policy/workflow/plan-implement`

The topic namespace is important, but the exact taxonomy does not need to be fixed exhaustively before implementation begins.

### 2. Audit and extract embedded policy choices

Audit existing user-facing templates and documents and extract opinionated choices into standalone policy documents where those choices are optional rather than universal.

The resulting core guidance should become more choice-agnostic where possible.

This extraction should prioritize high-value topics first, including:

- git / scm behavior
- commit and pull request behavior
- workflow handling
- testing and type-checking posture
- toolchain / packager preferences
- review strictness and autonomy boundaries

The audit may surface additional policy topics, which are in scope for extraction where valuable.

### 3. Support policy selection using existing configuration concepts

Policies remain plain documents. This change does not introduce a new policy object model.

Instead, policy selection should build on existing mechanisms:

- categories
- collections
- profiles
- project configuration

The system should provide a practical way to compose active policy documents without requiring users to rewrite the default document set manually.

### 4. Support selected-policy guide resolution

Where a guide resource refers to a policy topic, for example `guide://policy/scm`, the system should resolve that topic according to the user's selected applicable policy material rather than exposing all alternatives at once.

This requires a selection model that can distinguish:

- available policy variants for a topic
- the active policy or policies currently applied to the project

### 5. Keep policy selection separate from guided onboarding

This change defines the policy corpus and selection model.

It does not yet implement the full onboarding experience that will:

- inspect the project
- ask the user guided questions
- recommend profiles, flags, and policies
- apply them automatically

That broader interaction layer belongs to `add-guided-onboarding`.

## Scope

In scope:

- default `policy` category
- policy-topic document organization
- extraction of embedded optional preferences from existing docs/templates
- making core guidance more neutral where practical
- policy-oriented collections or starter composition support
- resolution rules for selected policy topics through guide resources

Out of scope:

- a full guided onboarding flow
- redesign of profiles/categories/collections into a new configuration system
- implementing every possible policy topic in one pass

## Success Criteria

- the default profile includes a `policy` category
- optional preferences are extracted from core docs/templates into policy documents for the highest-value topics
- users can compose selected policies using existing project configuration concepts
- `guide://policy/<topic>` can resolve to the selected applicable policy guidance for that topic
- core guidance becomes more choice-agnostic where optional preferences were previously embedded

## Impact

- Affected specs:
  - `project-config`
  - `help-template-system`
  - `mcp-resources-guide-scheme`
- Affected code:
  - default profile templates
  - policy/category/collection configuration handling
  - guide resource resolution
  - user-facing templates and documents that currently embed optional preferences
