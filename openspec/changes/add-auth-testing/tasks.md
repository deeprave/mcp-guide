# Tasks

## 1. Compatibility fixture and platform trust support

- [ ] 1.1 In `auth-guide`, add an opt-in compatibility-test profile that installs Guide with its `auth-ref` extra and accepts explicit Guide revision/package inputs; verify the profile can report both tested revisions without exposing credentials.
- [ ] 1.2 Implement disposable process fixtures for the provider database, public account administration, token issuance, Guide HTTPS process, free ports, and redacted subprocess diagnostics; verify cleanup runs after a deliberately failed scenario.
- [ ] 1.3 Implement Linux and macOS native trust-store fixture adapters that install and remove an ephemeral test CA without passing a Guide CA override; verify each adapter can distinguish trusted and untrusted provider certificates.

## 2. Published-boundary compatibility scenarios

- [ ] 2.1 Add black-box MCP scenarios for missing and invalid bearer evidence, ordinary-user authorisation, and administrative authorisation; verify the returned Guide result codes and protected effects.
- [ ] 2.2 Add a single-session bearer-isolation scenario that succeeds as admin then fails with absent and ordinary-user evidence; verify no later request performs the administrative effect.
- [ ] 2.3 Add a provider-unavailability scenario after Guide has started; verify unprotected MCP operations still work and protected operations return `authentication_unavailable` without an effect.
- [ ] 2.4 Add trusted and untrusted provider-certificate scenarios; verify the trusted native-store path succeeds and the untrusted path fails closed without disabled TLS validation.

## 3. CI and developer use

- [ ] 3.1 Add dedicated Linux and macOS CI jobs for the compatibility profile, retaining redacted failure diagnostics and keeping the suite outside the default unit-test command; verify both jobs run the identical scenario set.
- [ ] 3.2 Document local and CI invocation, required provider/Guide revision inputs, native trust-store cleanup, and the deliberate Windows deferral; verify the documented Linux and macOS commands run in their corresponding environments.
- [ ] 3.3 Run the compatibility suite against pinned compatible current revisions of both projects on Linux and macOS; record successful job evidence before making the jobs required.

## Workflow follow-up

- Review the cross-project implementation in both repositories, then synchronise and archive this change after the project review requirements are satisfied.
