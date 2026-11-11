# Design

## Context

Guide currently mixes two separate facts: whether the OpenSpec executable is installed, and whether the active project can resolve an OpenSpec store. It checks the former with `openspec --version`, but answers the latter by asking the client to inspect a worktree-local `openspec/` directory and its `config.yaml` and `changes` entries.

That layout is not authoritative. OpenSpec resolves a store from the active directory, including ancestor installations and named-store configuration. The client can therefore run OpenSpec successfully for a project whose own worktree contains no `openspec/` directory.

## Goals / Non-Goals

**Goals:**

- Treat OpenSpec CLI results from the bound project as the authority for executable availability, store resolution, changes, and resolved artifact paths.
- Keep project OpenSpec opt-in and the existing machine-wide 24-hour version check.
- Remove OpenSpec-specific client filesystem probes and path construction from task handling and rendered guidance.
- Retain efficient session-local changes caching without relying on client filesystem metadata.

**Non-Goals:**

- Discover or parse OpenSpec store configuration in Guide.
- Implement a new named-store protocol or reproduce OpenSpec's ancestor-search algorithm.
- Change OpenSpec CLI behaviour, store selection, or the user's project flag outside the existing enablement flow.

## Decisions

### Separate CLI availability from project-store resolution

`openspec --version` remains the machine-wide, 24-hour cached executable check. An explicit project enable transition additionally runs a CLI command from the bound project, initially `openspec list --json`, to determine whether that invocation resolves a usable store. The latter is project and client-context specific; it is not persisted as global availability.

Guide will not inspect `openspec/config.yaml`, list `openspec/changes`, or walk ancestor directories. Reimplementing discovery would diverge from the CLI and cannot support future store mechanisms. A successful empty list is a valid resolution. A CLI failure produces the existing initialisation guidance and leaves the user's explicit OpenSpec selection intact; Guide does not mutate project configuration in response to a transient or missing store.

### Make structured CLI replies the template data boundary

OpenSpec task responses continue to arrive through named structured imports such as `.openspec-changes.json` and `.openspec-status.json`. They are command results, not filesystem documents. The task will correlate list replies solely with its refresh generation, removing the preceding directory-list response and mtime handshake.

Workflow and command templates will run the appropriate CLI command and use its returned data, including resolved artifact locations where OpenSpec provides them. They will not construct `openspec/changes/<id>/...` paths or ask the agent to read a presumed local configuration file.

### Use TTL and explicit invalidation for change data

The changes cache remains session-local and keeps its one-hour TTL. `guide://_openspec/list?force` starts a new generation and replaces any cached list once its matching CLI reply arrives. Mutating commands retain the explicit forced-refresh recommendation. No OpenSpec filesystem event or directory mtime participates in cache validity.

### Preserve passive ordinary binding

Ordinary session binding and reconnect remain passive: they can reuse current global CLI-version state but do not issue a project-store or changes request. The project-store check occurs only after an explicit OpenSpec enable transition, while commands and templates obtain change data only on demand.

## Risks / Trade-offs

- [A project is moved or its ancestor store changes while a list cache is valid] → TTL expiry and explicit refresh after mutations provide bounded freshness without duplicating the CLI's discovery logic.
- [CLI errors lack a stable machine-readable reason for every version] → Guide presents the initialisation resource for an unsuccessful project-resolution command and preserves the raw formatted CLI error where available.
- [A CLI result contains an unfamiliar future store layout] → Guide treats it as opaque structured output rather than deriving paths from it, maintaining forward compatibility.

## Migration Plan

1. Replace OpenSpec filesystem probes and their directory-event correlation with CLI-result-only handling.
2. Revise the affected templates to remove assumed local OpenSpec paths and use CLI results or CLI-provided resolved locations.
3. Retire directory-mtime cache metadata and coverage, then verify the revised enablement, on-demand list, forced refresh, and inherited-store flows.
4. Existing project flags and cached version state remain compatible; no configuration migration is required.
