# Change: Add Content Delivery Analytics

## Why

There is currently no visibility into which guide content is actually being used. Content authors have no way to know which categories, collections, and documents are accessed per session, or how frequently — making it impossible to identify stale or underused documents or to prioritise high-value content. An opt-in analytics system would give authors actionable data without compromising the default zero-overhead operation.

## What Changes

### 1. Add an `analytics` feature flag

Add a new `analytics` feature flag (boolean, default off). When enabled, the system records content access events locally per project. No data leaves the machine; this is purely local observability.

### 2. Record content access events

When analytics is enabled, each document served to an agent is recorded with: document path, category, collection (if applicable), timestamp, and session identifier. Events are appended to a local log file (path configurable via `analytics-path` flag, defaulting to `.guide/analytics.jsonl`).

### 3. Add a `:stats` command

Add a new `:stats` prompt command that reads the local analytics log and surfaces:
- most-accessed documents in the current project (by count)
- documents not accessed in the last N sessions
- per-category access breakdown

### 4. Keep analytics strictly opt-in and local

Analytics MUST be disabled by default. The log file MUST be written only to the project's own filesystem under a path subject to `allowed_write_paths` validation. No telemetry, no network calls.

## Impact

- Affected specs: new `content-analytics` capability
- Affected code: content serving pipeline (access event emission), new analytics writer, new `:stats` command template, feature flag registration
