## 1. Client-path policy

- [x] 1.1 Add global tri-state sharing policy and LazyPath.client_resolve(), covering verified shared, unverified and disabled paths without changing server-owned resolution.
- [x] 1.2 Initialise stdio as unverified and HTTP/HTTPS as disabled; ensure HTTP/HTTPS never schedules a probe.
- [x] 1.3 Route initial binding, root switching, URI decoding, root identity and inherited-PWD bootstrap through the policy; preserve root-relative switching only when verified.

## 2. One-shot shared-filesystem verification

- [x] 2.1 Register a one-shot task after initial absolute-root binding, reserve one global attempt and exclusively create a unique probe file containing a random challenge.
- [x] 2.2 Queue one read-and-send instruction without revealing expected contents; start the 60-second timeout from outgoing-response dispatch notification rather than queue insertion.
- [x] 2.3 Intercept the exact probe response before ordinary file handling, validate contents and record the global sharing result.
- [x] 2.4 Clean up the probe, queued/tracked instruction and subscriptions after success, mismatch, failure, timeout or Session disposal; leave no recurring task or automatic retry.
- [x] 2.5 Verify lifecycle behaviour using existing task/acknowledgement test patterns, including delayed delivery, unrelated replies, HTTP exclusion and terminal cleanup.

## 3. Documentation

- [x] 3.1 Update user and agent documentation for verified stdio shorthand, HTTP/HTTPS absolute-only policy, Docker/remote examples, initial binding, dispatch-based timeout and the same-user/environment assumption.

Full-suite and pre-commit checks remain normal repository hygiene, not OpenSpec
implementation tasks.
