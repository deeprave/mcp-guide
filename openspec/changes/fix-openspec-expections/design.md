# Design

## Context

Guide currently mixes whether the OpenSpec executable is installed with a separate, invalid attempt to validate an active project's store. It checks the former with `openspec --version`, but answers the latter by asking the client to inspect a worktree-local `openspec/` directory and its `config.yaml` and `changes` entries.

That layout is not authoritative. OpenSpec resolves a store from the active directory, including ancestor installations and named-store configuration. Guide does not need to reproduce or preflight that behaviour: it invokes the CLI only when it needs CLI output.

## Goals / Non-Goals

**Goals:**

- Treat OpenSpec CLI results from the bound project as the authority for changes and resolved artifact paths when those are needed.
- Keep project OpenSpec opt-in and the existing machine-wide 24-hour version check.
- Remove OpenSpec-specific client filesystem probes, store validation, and path construction from task handling and rendered guidance.
- Retain efficient session-local changes caching without relying on client filesystem metadata.

**Non-Goals:**

- Discover or parse OpenSpec store configuration in Guide.
- Implement a new named-store protocol or reproduce OpenSpec's ancestor-search algorithm.
- Change OpenSpec CLI behaviour, store selection, or the user's project flag outside the existing enablement flow.

## Decisions

### Use the CLI on demand, without project-store validation

`openspec --version` remains the machine-wide, 24-hour cached executable check. Enabling OpenSpec for a project does not run a project-scoped CLI command or otherwise determine whether that project resolves a usable store.

Guide will not inspect `openspec/config.yaml`, list `openspec/changes`, walk ancestor directories, or preflight a CLI command. Reimplementing discovery would diverge from the CLI and cannot support future store mechanisms. When a consumer needs changes, Guide runs `openspec list --json` from the session's active worktree; a successful empty list is valid, while an error is handled by that consumer without mutating the user's explicit OpenSpec setting.

### Make structured CLI replies the template data boundary

OpenSpec task responses continue to arrive through named structured imports such as `.openspec-changes.json` and `.openspec-status.json`. They are command results, not filesystem documents. The task will correlate list replies solely with its refresh generation, removing the preceding directory-list response and mtime handshake.

Workflow and command templates will run the appropriate CLI command and use its returned data, including resolved artifact locations where OpenSpec provides them. They will not construct `openspec/changes/<id>/...` paths or ask the agent to read a presumed local configuration file.

### Use TTL and explicit invalidation for change data

The changes cache remains session-local and keeps its one-hour TTL. `guide://_openspec/list?force` starts a new generation and replaces any cached list once its matching CLI reply arrives. Dispatching a mutation-capable OpenSpec command invalidates cached OpenSpec results but does not request replacement data; a later consumer requests the CLI result it needs. No OpenSpec filesystem event or directory mtime participates in cache validity.

### Preserve passive ordinary binding

Ordinary session binding, reconnect, and an explicit OpenSpec enable transition remain passive: they can reuse current global CLI-version state but do not issue a project-scoped OpenSpec request. Commands and templates obtain change data only on demand.

## Risks / Trade-offs

- [A project is moved or its ancestor store changes while a list cache is valid] → TTL expiry and explicit refresh after mutations provide bounded freshness without duplicating the CLI's discovery logic.
- [CLI errors lack a stable machine-readable reason] → The consumer that requested the CLI result preserves the formatted CLI error where available and does not mutate the project's enabled setting.
- [A CLI result contains an unfamiliar future store layout] → Guide treats it as opaque structured output rather than deriving paths from it, maintaining forward compatibility.

## Migration Plan

1. Replace OpenSpec filesystem probes and their directory-event correlation with CLI-result-only handling.
2. Revise the affected templates to remove assumed local OpenSpec paths and use CLI results or CLI-provided resolved locations.
3. Retire directory-mtime cache metadata and retain the revised passive enablement, on-demand list, and forced-refresh behaviour.
4. Existing project flags and cached version state remain compatible; no configuration migration is required.
