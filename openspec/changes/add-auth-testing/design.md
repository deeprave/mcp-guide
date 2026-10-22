# Design

## Context

Guide's `auth-ref` adapter and `auth-guide` are developed in separate
repositories. Their focused tests validate each side independently but do not
prove that the released configuration, TLS, token, and MCP boundaries work
together. The compatibility requirements are defined in
`auth-provider-compatibility-testing`.

## Goals / Non-Goals

**Goals:**

- Exercise the two services as independently started processes through public
  interfaces.
- Run the same behavioural scenarios on Linux and macOS.
- Verify real operating-system trust-store use without introducing a
  Guide-specific certificate override.
- Make failures diagnosable through retained subprocess output while ensuring
  bearer values and response bodies are not emitted in test assertions or logs.

**Non-Goals:**

- Testing Windows in this change.
- Replacing either project's focused unit tests or testing an interactive login
  user interface.
- Adding production dependencies, test-only authentication modes, or provider
  lifecycle management to Guide.
- Establishing a generic multi-provider conformance framework before a second
  provider needs one.

## Decisions

### Own the end-to-end fixture in `auth-guide`

`auth-guide` owns its service lifecycle, disposable database bootstrap,
administration API, and token issuance. Its repository SHALL host the primary
compatibility test and invoke Guide as an installed dependency or isolated
checkout with the `auth-ref` extra. This keeps the test fixture aligned with
the provider's public deployment interface.

A lightweight Guide CI smoke job MAY later run the same suite against a pinned
`auth-guide` image or release. It is not required for the first implementation.

Alternatives considered:

- Owning the suite in Guide would make the provider's service fixture a
  cross-repository implementation detail.
- A new shared test package would add versioning and release coordination before
  it provides value.

### Use black-box process orchestration

The fixture SHALL create temporary directories, a disposable provider database,
ephemeral accounts, certificates, and free local ports. It SHALL start
`auth-guide`, provision ordinary and administrative accounts through its public
administration interface, obtain bearer evidence through its public token flow,
then start Guide configured with `--auth-provider auth-ref` and `AG_ADDRESS`.
It SHALL interact with Guide only through a Streamable HTTP MCP client.

Protected operations chosen by the fixture SHALL be observable, isolated to
temporary Guide state, and safe to repeat. The fixture SHALL use an unprotected
operation to confirm lazy availability separately from protected operations.

### Verify trust through the native operating-system store

The test fixture SHALL generate a test CA and provider certificate. Linux CI
shall install the CA into the disposable job/container's native CA store; macOS
CI shall install it into the ephemeral runner's test/user trust store using the
platform-native facility, then remove it during cleanup. Guide shall not receive
a CA-bundle argument or disabled certificate verification.

A separate untrusted-certificate scenario SHALL use an endpoint not trusted by
that store and assert the safe protected-operation failure. The certificate
material and trust-store updates are CI fixture concerns, not production
configuration.

Alternative considered: passing a temporary CA file to HTTPX or Guide. Rejected
because it would not test the production operating-system trust boundary.

### Preserve per-request evidence coverage

Within one established MCP session, the suite SHALL issue an admin-protected
request with administrative evidence, then repeat it with absent and ordinary
user evidence. This specifically tests request-context isolation rather than
only independent connections.

### Run an explicit integration CI profile

The compatibility suite SHALL be marked separately from regular unit tests and
run in dedicated Linux and macOS CI jobs. Local invocation SHALL be documented
and must perform the same process setup. Windows is excluded from the matrix
until a follow-up change defines native trust-store handling and process
orchestration there.

## Risks / Trade-offs

- [Native trust-store installation differs by platform] → Keep the scenario
  fixture behind a small platform adapter, use ephemeral CI runners, and require
  cleanup verification on macOS.
- [Process tests can be slower or fail to release ports] → Use bounded startup,
  deterministic temporary paths, retained redacted logs, and `finally` cleanup.
- [A current checkout of the other repository is unavailable locally] → Allow a
  pinned package/image input for CI and document the required local source path
  or release version.
- [Cross-repository API changes need coordinated validation] → Pin the tested
  Guide and provider revisions in each CI run and expose those revisions in job
  metadata.

## Migration Plan

1. Add the integration fixture and Linux/macOS CI profile in `auth-guide`.
2. Add the corresponding Guide install/test input and documentation in this
   repository.
3. Run the suite against the current released or pinned compatible revisions.
4. Gate compatible changes on the dedicated profile after it proves stable.

Rollback consists of removing the CI gate while retaining existing focused unit
tests; it does not affect production authentication behaviour.
