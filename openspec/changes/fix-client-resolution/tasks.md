## 1. Client-path policy

- [ ] 1.1 Add process-wide tri-state client-filesystem configuration and `LazyPath.client_resolve()`; verify unit tests cover unconfigured, shared, and separate states.
- [ ] 1.2 Add an explicit server startup CLI/environment configuration surface that sets the client-filesystem state independently of transport; verify startup tests cover both configured values and the default.
- [ ] 1.3 Update existing client-path utilities and root-identity hashing to use lexical client resolution where applicable; verify server-visible symlinks cannot collapse distinct client root identities.

## 2. Project and session integration

- [ ] 2.1 Route initial project binding and `file://` URI decoding through client resolution; verify percent-encoded URIs and separate-filesystem absolute roots are accepted without host expansion.
- [ ] 2.2 Route retained root rebinding through client resolution, preserving root-relative paths only for shared filesystems; verify separate and unconfigured deployments reject relative and user-anchored roots with the standard invalid-path result.
- [ ] 2.3 Gate the opt-in inherited-PWD bootstrap on client-path validity; verify separate and unconfigured deployments remain unbound even when `MG_USE_PWD` is enabled.

## 3. Documentation and verification

- [ ] 3.1 Update agent-facing installation and protocol/session documentation to explain deployment-level filesystem sharing, absolute roots for separate filesystems, and the distinction from server-owned docroot/config paths; verify links and examples are accurate.
- [ ] 3.2 Run targeted client-resolution, session, request-context, and project-selection tests in a foreground PTY; verify all pass.
- [ ] 3.3 Run the full test suite in a foreground PTY and `openspec validate fix-client-resolution --strict`; verify both pass.
