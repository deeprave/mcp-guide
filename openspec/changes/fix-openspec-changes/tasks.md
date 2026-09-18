## 1. Lazy changes-list collection

- [x] 1.1 Remove the project-detection path that queues `openspec list --json`, and verify OpenSpec initialisation leaves no changes-list instruction pending.
- [x] 1.2 Use the explicit OpenSpec list command as the sole demand-driven changes-data path when a consumer requires an absent or invalid cache, and verify passive context construction does not request a refresh.

## 2. Cache validity

- [x] 2.1 Store the client-observed `openspec/changes` modification time with each cached list and verify an unchanged directory reuses it within the TTL.
- [x] 2.2 Invalidate and refresh cached changes when the TTL expires or the observed directory modification time changes, and verify unavailable metadata is treated as stale.
- [x] 2.3 Preserve activation-owned cache invalidation and project-switch cleanup for changes data, verified with focused task lifecycle tests.

## 3. Consumer integration and verification

- [x] 3.1 Route every OpenSpec changes-data consumer through the demand-driven cache path and verify explicit OpenSpec list rendering remains correct.
- [x] 3.2 Run focused OpenSpec task, template-context, and command tests to verify no unrelated Guide response triggers a changes-list request.
