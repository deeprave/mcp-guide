# Tasks

## 1. Backend Alignment and Regression Coverage

- [x] 1.1 Confirm `migrate-hypercorn-asgi` is deferred pending upstream Uvicorn dependency resolution; implement independently against the existing Uvicorn backend without introducing a second backend.
- [ ] 1.2 Add behavioural regressions for `[::]`, localhost/hostless URLs, IPv4 literals, specific IPv6 addresses and dual-family hostname resolution; verify the new dual-stack expectation fails before implementation while existing bind expectations remain unchanged.

## 2. Dual-Stack Listener and Lifecycle

- [ ] 2.1 Implement explicit dual-stack wildcard listening in the HTTP transport; verify real IPv4 and IPv6 clients can initialise MCP through the same endpoint, including HTTPS with isolated test certificates and the existing authorisation policy.
- [ ] 2.2 Add clear startup failure for unsupported or unsuccessful dual-stack binds and use the existing common cleanup path; verify failure, cancellation and shutdown release the listener and allow the address/port to be rebound.

## 3. Documentation and Verification

- [ ] 3.1 Update installation and Docker guidance with `[::]` dual-stack examples, the IPv4-only meaning of `0.0.0.0`, hostname/localhost behaviour and the breaking exposure change; manually check the examples against observed transport behaviour without source-text tests.
- [ ] 3.2 Run focused transport tests and the full pytest suite in foreground terminals, then run repository validation hooks; verify results and report any unrelated failures or expected branch-guard rejection.
- [ ] 3.3 Run `openspec validate add-dual-stack-http --strict --no-interactive` and `git diff --check`; verify both pass and that the completed implementation still preserves optional authentication and localhost defaults.
