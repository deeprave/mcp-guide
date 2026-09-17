## 1. Lazy changes-list collection

- [ ] 1.1 Remove the project-detection path that queues `openspec list --json`, and verify OpenSpec initialisation leaves no changes-list instruction pending.
- [ ] 1.2 Introduce a single demand-driven changes-data path that queues at most one refresh when a consumer requires an absent or invalid cache, and verify concurrent consumers do not duplicate the request.

## 2. Cache validity

- [ ] 2.1 Store the client-observed `openspec/changes` modification time with each cached list and verify an unchanged directory reuses it within the TTL.
- [ ] 2.2 Invalidate and refresh cached changes when the TTL expires or the observed directory modification time changes, and verify unavailable metadata is treated as stale.
- [ ] 2.3 Preserve activation-owned acknowledgement, cache invalidation, and project-switch cleanup for a pending on-demand refresh, verified with focused task lifecycle tests.

## 3. Consumer integration and verification

- [ ] 3.1 Route every OpenSpec changes-data consumer through the demand-driven cache path and verify explicit OpenSpec list rendering remains correct.
- [ ] 3.2 Run focused OpenSpec task, template-context, and command tests to verify no unrelated Guide response triggers a changes-list request.
