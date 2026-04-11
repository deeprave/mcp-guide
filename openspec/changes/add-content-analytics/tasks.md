## 1. Add analytics feature flags
- [ ] 1.1 Add `analytics` boolean feature flag (default: false)
- [ ] 1.2 Add `analytics-path` string flag (default: `.guide/analytics.jsonl`)
- [ ] 1.3 Validate `analytics-path` against `allowed_write_paths` security policy on flag set
- [ ] 1.4 Register both flags in feature flag configuration

## 2. Implement analytics writer
- [ ] 2.1 Create async `AnalyticsWriter` that appends JSONL events to the configured path
- [ ] 2.2 Define event schema: `{"ts": ISO8601, "session": str, "path": str, "category": str, "collection": str | null}`
- [ ] 2.3 Ensure writes are non-blocking (fire-and-forget via task queue)
- [ ] 2.4 Suppress all writer errors silently — analytics failures must never affect content delivery

## 3. Instrument content serving pipeline
- [ ] 3.1 Identify the point in the content serving pipeline where documents are finalised for delivery
- [ ] 3.2 Emit an access event per document when `analytics` flag is enabled
- [ ] 3.3 Include category and collection metadata from `FileInfo` / content context

## 4. Implement `:stats` command
- [ ] 4.1 Create `_commands/stats.mustache` command template
- [ ] 4.2 Implement analytics reader: parse JSONL log, aggregate by document path
- [ ] 4.3 Surface top-N most accessed documents, per-category counts, and never-accessed documents
- [ ] 4.4 Add `--since` flag to filter by number of recent sessions or a date
- [ ] 4.5 Expose stats data in template context for rendering

## 5. Tests and validation
- [ ] 5.1 Unit tests for `AnalyticsWriter` (write, rotate, error suppression)
- [ ] 5.2 Unit tests for analytics reader aggregation logic
- [ ] 5.3 Validate change with `openspec validate add-content-analytics --strict --no-interactive`
