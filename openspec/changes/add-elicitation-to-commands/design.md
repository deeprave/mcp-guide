## Context

See [proposal.md](proposal.md) for motivation. The current resolver is generic in
its form parsing but is named for skills and invoked only for selected skill
`SKILL.md` entrypoints. Command templates already have frontmatter, URI keywords,
and request context, so a second command-specific mechanism would duplicate the
same protocol and validation work. The current flat declarations request every
missing form at once and have no way to express a follow-up choice.

Rendered documents already combine some frontmatter properties from partials, but
interactive input must be known before an entrypoint body is rendered. A partial
that exists only to contribute input properties therefore needs an explicit
property-only path.

## Goals / Non-Goals

**Goals:**

- Use one declarative form model and one resolver for skill and command entrypoints
- Support deterministic conditional follow-up forms without entrypoint-name logic
- Compose input declarations from eligible parent and partial frontmatter before
  interactive rendering
- Retain the existing non-interactive document-serving path

**Non-Goals:**

- Elicit input while serving ordinary category, collection, or multi-document
  content
- Add arbitrary JSON Schema conditionals, object properties, arrays, or a general
  expression language
- Execute a skill script, or persist elicitation data to project configuration
- Infer a partial's interaction properties from an unlisted dynamic partial name

## Decisions

### Move the resolver to an entrypoint-neutral domain

Move the current skill-named form parser and resolver into an
entrypoint-neutral elicitation module. Its public input is the effective
frontmatter declaration, supplied URI keywords, and the request context; it has
no knowledge of command or skill names. Command and skill dispatch both use the
same pre-render resolution result.

This retains the existing primitive field and URI semantics while making the
shared boundary explicit. A command-specific implementation was rejected because
it would drift in validation, capability negotiation, and response handling.

### Use a small declarative branching language

Each named form remains a `message` and primitive object `schema`. A form may add
a `when` mapping whose keys name earlier URI or accepted form properties and whose
values are lists of permitted primitive values:

```yaml
elicitation:
  review-target:
    message: Choose the review target.
    schema:
      type: object
      properties:
        mode:
          type: string
          enum: [uncommitted, main, branch, pull-request]
      required: [mode]
  review-reference:
    when:
      mode: [branch, pull-request]
    message: Enter the branch or pull request.
    schema:
      type: object
      properties:
        reference:
          type: string
      required: [reference]
```

All `when` keys must match. A condition with an unknown value is not yet
applicable; a condition with a known non-matching value is skipped. Form and
property names are globally unique in the effective declaration. This supports
the needed decision tree without creating an executable expression language or
ambiguous ordering rules.

### Resolve modern branching with an integrity-protected continuation state

For modern MCP input-required responses, construct a short-lived opaque
continuation state that binds the selected entrypoint identity, original request
arguments, accepted primitive values, and completed form identifiers to the
current Guide interaction. Protect the state against modification and reject it
when it does not match the retried command or skill request. The client echoes it
verbatim as required by the MCP input-result contract.

On each retry, merge validated URI keywords, the protected accumulated values, and
newly accepted input responses, then recompute applicable forms. Return another
input-required result only when a newly applicable form remains unresolved. The
state is process-lifetime transient and is not stored in project configuration,
task queues, rendering caches, or the workflow file. A restart invalidates a
continuation naturally.

For legacy MCP elicitation, collect currently applicable forms sequentially using
the existing FastMCP path and re-evaluate conditions after each accepted response.
For non-eliciting clients and internal calls, return explicit guidance for the
currently applicable unresolved keyword set. This avoids pretending a client can
complete an unavailable interaction.

### Collect interactive partial properties before rendering bodies

Add `DocumentElicitation` as a composable document property alongside the existing
frontmatter-property handlers. The property owns declaration parsing, identifier
and field collision checks, and source-aware combination. It exposes an effective
form set to the neutral resolver; request dispatch remains responsible for MCP
interaction.

An entrypoint's explicit frontmatter `partials` list is the pre-render property
inclusion mechanism. Each listed partial is resolved with existing containment and
`requires-*` rules, then contributes its document properties even if its body is
not interpolated. This allows a frontmatter-only partial to carry shared forms or
future composable properties. A listed partial's body is emitted only when the
parent explicitly renders it through the ordinary Mustache partial mechanism.

Existing inline partial rendering and its output behaviour remain unchanged. An
author who needs an inline partial to contribute an elicitation declaration before
rendering must also list it in parent frontmatter. This keeps interaction planning
deterministic and avoids executing or rendering a body merely to discover its
metadata.

### Preserve URI and prompt entrypoint semantics

Command URI resources, `read_resource`, native resources, and underscore-prefixed
Guide prompt commands enter the same command dispatch path. That path must return
the modern input-required result unchanged, as the skill path already does. Once
all applicable forms are satisfied, it renders through the existing command
context, with supplied and accepted values merged into `kwargs` and `raw_kwargs`.

Ordinary document requests deliberately bypass this preflight. Their result is
content, not an interactive operation, even when a document happens to carry an
`elicitation` key.

### Document the authoring boundary

Extend developer documentation to cover command declarations, `when` branching,
frontmatter-only partials, continuation/retry behaviour, and the explicit
non-interactive document boundary. Keep the skills authoring guide as the shared
frontmatter reference rather than duplicating schema details across documents.

## Risks / Trade-offs

- [A malformed or colliding partial declaration creates an ambiguous form] → fail
  the selected interactive entrypoint with a clear diagnostic before requesting
  input
- [A continuation token is replayed for another entrypoint or modified] → bind and
  integrity-protect it against the active interaction and original request
- [Branching grows into a general rules engine] → limit `when` to primitive
  equality membership over declared properties
- [An author expects an unlisted dynamic partial to add a form] → document that
  pre-render input contributors must be explicitly listed in frontmatter
- [A non-eliciting client cannot complete an interactive command] → return the
  currently required URI keywords instead of rendering partial assumptions

## Migration Plan

1. Keep existing skill `elicitation` frontmatter valid and route it through the
   neutral resolver unchanged
2. Add command and partial support behind the same declaration contract
3. Add bundled command examples only where a command benefits from interaction
4. Update developer documentation and release notes
5. Roll back by removing declarations from commands or partials; undeclared
   entrypoints retain their existing rendering path
