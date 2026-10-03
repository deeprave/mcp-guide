# Tasks

## 1. Establish the command boundary

- [ ] 1.1 Audit every server-side effect reachable from shared command dispatch, including pre-render elicitation and command-specific branches; record whether it mutates protected project, global, permission, document, or export state and verify the result against the implementation.
- [ ] 1.2 Add isolated behavioural coverage showing that an unauthenticated provider-backed caller can render a guidance-only command through both the Guide prompt and `guide://_...` command URI routes, without testing production template text.
- [ ] 1.3 Verify that any client action described by a rendered command remains subject to the invoked tool's existing user or admin scope check.

## 2. Apply only demonstrated command policy

- [ ] 2.1 If the audit identifies a command with a direct protected server-side mutation, add its explicit server-owned `AuthScope` enforcement in the shared command route before that action and verify identical forbidden/not-authorised outcomes for prompt and command-URI invocation.
- [ ] 2.2 If no direct protected command mutation exists, retain no command-level scope gate; document the decision in ADR-014 and the authentication change artefacts, and verify that unauthenticated command inspection remains available.

## 3. Validate the contract

- [ ] 3.1 Run the focused command, prompt, resource, and authentication tests in the foreground and verify the new delta specifications with `openspec validate add-command-auth --strict`.
