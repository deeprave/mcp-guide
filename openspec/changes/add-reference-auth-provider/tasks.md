# Tasks

## 1. Establish the provider contract and optional package boundary

- [ ] 1.1 Reconcile `add-mcp-authentication` with the final provider contract: one provider-selection option, named-operation decisions, `allow`/`forbidden`/`not_authorised`, bounded capability availability, no raw scopes or principals in Guide handlers, and no export-state capability; verify strict OpenSpec validation passes for both changes.
- [ ] 1.2 Add the optional `oidc` provider entry point and dependency group, with provider-owned environment configuration and lazy loading; verify a normal installation and a server without provider selection do not import OIDC dependencies.
- [ ] 1.3 Implement the Guide-side OIDC adapter's issuer discovery, JWKS verification, named-operation mapping, hand-off result, expiry handling, and key invalidation; verify unit tests cover valid, missing, malformed, expired, and insufficient-access bearers without exposing decoded claims to handlers.

## 2. Build the independent reference identity provider

- [ ] 2.1 Select and integrate maintained standards and cryptography libraries for the reference OIDC application; document the supported issuer, signing, and password-verifier configuration and verify dependency installation succeeds.
- [ ] 2.2 Implement the independently runnable application with persistent local users, Argon2id password verifiers, asymmetric signing keys, OIDC discovery, JWKS publication, short-lived bearer-token issuance, and HTTPS login/token-provisioning hand-off; verify Guide does not start or depend on the application's process lifecycle.
- [ ] 2.3 Add the administrator command to bootstrap, list, disable, reset passwords for, and assign user/admin access to accounts; verify plaintext passwords and issued tokens are neither persisted nor emitted in normal command output or logs.

## 3. Prove the reference pair

- [ ] 3.1 Add end-to-end tests with a disposable reference issuer and Guide remote transport; verify lifecycle, discovery, valid user/admin access, missing/expired/insufficient bearer results, hand-off, disabled accounts, and signing-key refresh.
- [ ] 3.2 Document separate deployment, HTTPS requirements, issuer/module configuration, user administration, client bearer configuration, rotation, rollback, and the reference application's operational limits; verify the documentation states that Guide never receives passwords or manages accounts.
- [ ] 3.3 Run `openspec validate add-reference-auth-provider --strict`, the targeted provider/application tests in the foreground, and the applicable formatting and type checks; verify all commands pass.
