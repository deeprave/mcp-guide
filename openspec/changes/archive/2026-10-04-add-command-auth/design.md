# Design

## Context

See [proposal.md](proposal.md) for the motivation. Both `guide://_...` command
resources and prompt command syntax converge on the same command handler after
request-context resolution. The handler discovers a template, resolves arguments
and elicitation, and renders content.

The completed audit finds no command that directly mutates project configuration,
global configuration, permission paths, or the document store. The one
command-specific state change prepares an OpenSpec refresh in the caller's
session task manager; the subsequent client filesystem callback is already an
intentionally unprotected, non-project-mutating interaction. Commands may
instruct a client to call tools, but those tool calls retain their own scope
checks.

## Audit Outcome

The user approved an audit-only closure on 2026-10-04. No implementation,
additional behavioural tests, ADR changes or canonical spec changes are required.
The proposed delta requirements are withdrawn rather than synced as hypothetical
command-enforcement functionality.

| Audited path or effect | Finding and boundary |
| --- | --- |
| Prompt command syntax, native command resources and tool-backed command URIs | All converge on `handle_command()` through the resolved request context. |
| Discovery, aliases, argument validation, elicitation and rendering | Read content or collect invocation-local input; do not call protected mutation handlers. |
| `openspec/list` preparation | Updates session-local refresh identifiers and cache state, not protected configuration or documents. |
| Response processing and task hooks | Deliver instructions; normal command responses do not dispatch document-ingestion events. Automatic detection metadata and ordinary callbacks remain intentionally unprotected. |
| Client instructions to invoke a mutating tool | The subsequent tool call independently checks its declared scope before the protected handler runs. |

The inspected enforcement points are `toolfunc()` and `_authorise_tool()` in
`src/mcp_guide/core/tool_decorator.py`. Provider-backed requests use the current
`RequestContext.authorisation`; a missing decision fails closed. User access
guards project/category/collection/profile changes and document storage; admin
access guards cloning, explicit permission-path tools and global configuration.
Project binding, ordinary callbacks and automatic document updates remain the
intentional exceptions defined by ADR-014.

`export_content` still adds a destination to `allowed_write_paths` under user
access. This is the documented temporary exception in ADR-014, not a command
bypass. `retire-export-metadata` task 2.1 already removes path approval and all
export configuration writes; that work stays outside this closure.

## Goals / Non-Goals

**Goals:**

- Establish a factual command-side-effect inventory before adding an
  authorisation gate.
- Preserve equivalent behaviour for prompt and command-URI invocation.
- Keep actual project, global, permission, document, and export operations
  protected at their existing tool boundaries.

**Non-Goals:**

- No scope declaration in command-template frontmatter.
- No generic resource or prompt authorisation mechanism without a direct
  protected operation to use it.
- No authentication provider, credential, transport, reverse-proxy, or
  client-filesystem policy changes.

## Decisions

### Treat rendering and guidance as non-mutating

Command rendering is not itself a protected operation merely because it can
recommend a protected tool. This keeps unauthenticated help, configuration
inspection, and onboarding guidance usable, while the later mutating tool call
is denied or allowed by its declared scope.

Alternative considered: require `user` for every command. Rejected because it
turns a read/guidance surface into an access gate and blocks legitimate
unauthenticated inspection without protecting an additional mutation.

### Keep the common command route as the future enforcement point

If a future audit identifies a command with a direct protected server-side
effect, its scope decision must occur in the shared command route after the
canonical command is resolved and before elicitation, command-specific work, or
rendering. This preserves identical results for the prompt, native resource,
and tool-backed command URI routes.

No generic hook, decorator parameter, or policy registry is introduced now.
Those would be speculative until a concrete command requires one. A future
change must define the command's server-owned policy and test both public
routes.

### Keep policy out of templates

The server, not a project-editable command template or its frontmatter, owns
the decision whether a direct operation requires a scope. Templates may use
the existing request-scoped `auth` predicates to give useful guidance, but
cannot make an unauthorised operation available.

## Risks / Trade-offs

- [A future command gains a direct mutation without an accompanying scope]
  → Require its change to identify the side effect and add shared-route
  enforcement before release.
- [A tool call is mistaken for command-side mutation] → Keep the tool as the
  sole enforcement boundary when the command only returns instructions.
- [Prompt and URI routes diverge] → A future change introducing a directly
  mutating command must test the shared authorisation boundary across routes.

## Migration Plan

No migration is required. Existing command output and unauthenticated command
inspection continue unchanged. If future direct command mutation is introduced,
its new scope boundary will fail closed for provider-backed callers and remain
unrestricted when no provider is configured.

The present change closes with documentation of the audit only. No tests were
added or run, and no runtime or canonical specification changes are made.
