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

## 4. Review follow-up

- [x] 4.1 Invalidate rendered OpenSpec template context when changes cache validity transitions, including directory-mtime changes and TTL expiry, with behavioural coverage.
- [x] 4.2 Route post-operation changes refreshes through the explicit OpenSpec list flow so every list is paired with fresh directory metadata.
- [x] 4.3 Document directory-mtime cache validity and directory-listing metadata in the cache-management and filesystem-tools specifications, then validate strictly.

## 5. Lazy context and forced refresh follow-up

- [x] 5.1 Keep OpenSpec data outside the materialised template-context cache so each consumer evaluates TTL and directory-mtime validity lazily, without a recurring task timer.
- [x] 5.2 Add forced OpenSpec-list refresh handling and direct successful OpenSpec mutations to `guide://_openspec/list?force`.
- [x] 5.3 Add focused behavioural coverage and update the cache-management and template-context specifications, then validate strictly.

## 6. Review follow-up: complete mutation and timer contracts

- [x] 6.1 Remove the obsolete recurring Timer Integration requirement from the cache-management delta.
- [x] 6.2 Direct successful proposal creation to `guide://_openspec/list?force`.

## 7. Review follow-up: correlate concurrent refresh replies

- [x] 7.1 Attach an opaque refresh identifier to paired changes-directory and
  OpenSpec-list replies, ignore superseded responses, and add out-of-order
  response coverage.
