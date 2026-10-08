# Tasks

## 1. Establish the provider contract and optional package boundary

- [x] 1.1 Reconcile `add-mcp-authentication` with the final provider contract: one provider-selection option; request-level `UserAuthorisation` with `user`/`admin` `AuthScope` values; `not_authorised` for missing or invalid authentication; `forbidden` for insufficient authenticated scope; `admin` satisfying `user`; no raw token, claim, or principal in Guide handlers; and no export-state capability. Verify strict OpenSpec validation passes for the reference change and canonical specifications.
- [ ] 1.2 Add the optional `auth-ref-oidc` provider entry point and dependency group, with provider-owned environment configuration and lazy loading; verify a normal installation and a server without provider selection do not import OIDC dependencies.
- [ ] 1.3 Implement the Guide-side `auth-ref-oidc` adapter's issuer discovery, JWKS verification, `UserAuthorisation` scope mapping, hand-off result, expiry handling, and key invalidation. In local-reference-provider mode, connect first, then start and own the provider process only when it is unavailable; fail startup when it cannot become ready. Verify unit tests cover valid, missing, malformed, expired, and insufficient-access bearers without exposing decoded claims to handlers.

## 2. Build the independent reference identity provider

- [ ] 2.1 Select and integrate maintained standards and cryptography libraries for the reference OIDC application; document the supported issuer, signing, and password-verifier configuration and verify dependency installation succeeds.
- [ ] 2.2 Implement the independently runnable application with a SQLCipher-encrypted SQLite user store through SQLAlchemy and a SQLCipher-capable DBAPI; persistent local users; Argon2id password verifiers; asymmetric signing keys; OIDC discovery; JWKS publication; short-lived bearer-token issuance; an authenticated management API; and HTTPS login/token-provisioning hand-off. Verify it can run independently and that the adapter starts and stops it only in configured local-reference-provider mode.
- [ ] 2.3 Add the administrator command as an authenticated management-API client to bootstrap, list, remove, securely set or reset passwords for, and assign user/admin access to accounts; verify it never opens the database and that plaintext passwords and issued tokens are neither persisted nor emitted in normal command output or logs.

## 3. Prove the reference pair

- [ ] 3.1 Add end-to-end tests with a disposable reference issuer and Guide remote transport; verify lifecycle, discovery, valid user/admin access, missing/expired/insufficient bearer results, hand-off, disabled accounts, and signing-key refresh.
- [ ] 3.2 Document separate deployment, HTTPS requirements, issuer/module configuration, user administration, client bearer configuration, rotation, rollback, and the reference application's operational limits; verify the documentation states that Guide never receives passwords or manages accounts.
- [ ] 3.3 Run `openspec validate add-reference-auth-provider --strict`, the targeted provider/application tests in the foreground, and the applicable formatting and type checks; verify all commands pass.
