# Change: Add External Issue Tracker Integration

## Why

The workflow system tracks `issue`, `tracking`, `description`, and `queue` fields in `.guide.yaml`, but populating them is entirely manual. Agents must be told the issue ID, tracking reference, and related context by the user each time. Teams using GitHub Issues, Linear, or Jira already have this information in their tracker — requiring it to be re-entered creates friction and risks divergence between the tracker and the workflow state.

Adding a `tracker` feature flag lets the system resolve live issue data from the configured tracker and auto-populate workflow fields, reducing setup overhead and keeping the workflow state aligned with the source of truth.

## What Changes

### 1. Add a `tracker` feature flag

Add a new project-level feature flag `tracker` that configures external issue tracker integration. The flag accepts a tracker type and connection parameters (e.g. repository or project identifier). Supported initial targets: GitHub Issues, Linear, Jira.

### 2. Extend `:workflow/issue` to resolve from tracker

When a tracker is configured, `:workflow/issue <id-or-url>` should attempt to resolve the given reference against the configured tracker and auto-populate `issue`, `tracking`, `description`, and optionally `queue` from the tracker response.

### 3. Add tracker-aware queue population

When transitioning to the next issue (`:workflow/reset` or `:workflow/issue --next`), if a tracker is configured, the system may suggest or auto-populate `queue` from open issues assigned to the current user or matching a configured filter.

### 4. Keep tracker integration opt-in and non-blocking

If the tracker is unavailable, unreachable, or returns no result, the workflow must continue to function exactly as it does today — tracker resolution is advisory. Failures must not prevent normal workflow operation.

## Impact

- Affected specs: `workflow-flags`, `workflow`
- Affected code: workflow flag parsing, workflow command templates, workflow context resolution, new tracker integration module
