## Context

See proposal.md for motivation. ADR-012 already places Session ownership in
GuideRuntime and keeps ConfigManager process-owned. The current runtime has
`_inflight_sessions` for ephemeral unbound work and `_sessions` for retained
instances, but it does not have an expiring collection. Request leases are
currently keyed only by owner, and request completion can unconditionally
re-retain its captured Session.

The current implementation mutates an existing bound Session and tries to clear
all derived state before reuse. That approach is superseded by this design.
The public interaction ID remains stable; the Python Session object need not.

## Goals / Non-Goals

**Goals:**

- Use the existing Session as the ownership boundary for project state and work.
- Give every bound Session an immutable root and configuration identity.
- Make one runtime operation replace the active instance and expire the old one.
- Allow existing operations to finish on their original project without granting
  them access to the replacement's mutable state.
- Reduce synchronisation to actual shared resources and short registry changes.

**Non-Goals:**

- A new ProjectScope, ProjectData lifecycle wrapper, actor framework or generic
  resource-registration framework.
- Multiple expiring instances for the same public ID, queued rapid switches or
  automatic retry of a rejected switch.
- Historical routing of client replies, binding-generation wire tokens, or
  protecting clients from submitting follow-up work for their former project.
- General optimistic concurrency, configuration revision tokens, or a broad
  redesign of simultaneous edits to the same project.
- Changing global OpenSpec CLI state ownership, initial-binding semantics, the
  deferred client-path resolver policy or protocol support.

## Decisions

### 1. Three runtime collections, one-way instance lifecycle

```text
unbound (ephemeral) -> bound (current for session_id) -> expiring -> disposed
```

Reuse the ephemeral collection for unbound request work and the active collection
for retained bound Sessions. Add an expiring collection keyed by the same
validated owner/public ID, with at most one entry per ID.

A switch prepares a new unbound instance, binds it once to the target, and
publishes it as the current bound instance. The previously bound instance moves
to expiring. An instance never returns from expiring to bound and is never
rebound to a different project.

Unbound describes the absence of a project binding, not necessarily the absence
of an ID: the initial FastMCP binding path can obtain a validated ID before
project binding completes. Such an instance is not retained as bound until its
initial binding succeeds. Unbound requests that never bind are disposed of when
their request work ends, as today.

This extends ADR-012's registry ownership; it does not introduce another
transport session or transfer state between different client owners.

### 2. Keep the selector contract

Exactly one of `name` or `path` is required. Name-only selection uses the current
root and supplied configuration name. Path-only selection uses the normalised
path and its basename. Resolve configurations by the existing strict
`(name, root_hash)` identity.

Preserve existing lexical absolute/relative path handling and local,
percent-decoded file URIs, including case-insensitive `file` and `localhost`.
Retain the already agreed user-anchor behaviour pending `fix-client-resolution`;
this redesign does not expand it. Unknown user anchors remain invalid input.

An unchanged name/root selection is a no-op when no expiry is pending. Check the
expiring-ID guard first: while an ID is expiring, reject a switch rather than
start another transition, including an otherwise unchanged selection.

Both name-only changes and root changes replace the bound instance.
`set_project` remains initial-binding-only and rejects a second initial bind.

### 3. Prepare, replace, activate

Runtime owns the operation; the outgoing Session does not change its own binding.

- Verify that the request's captured Session is the current bound instance and
  the owner has no expiring entry. Validate and resolve the target.
- Prepare a fresh Session with the target binding and fresh owned components.
  Do not expose it to incoming requests or start recurring work while preparing.
  Copy only `session_id`, available client/agent connection metadata and the
  establishment-log marker; never copy mutable project/task/cache state.
- Recheck the expected current instance and absence of an expiring entry after
  asynchronous preparation. Publish the new active entry, mark/move the old
  entry to expiring, and stop admission of new work to the old instance in one
  short, non-awaiting registry operation.
- Run the replacement's normal initial-bound activation, not a pre-switch/reset
  sequence on the old instance. Finish the switch response using the returned
  replacement Session and its queue.
- Drain the old instance independently of the switch response. The initiating
  request still holds the old instance until its final release, so switch must
  not wait for that request to finish itself.

Target-validation or preparation failure leaves the active Session unchanged
and disposes of the unpublished candidate. Successful publication is not undone
by an old request's completion or cancellation. Post-publication activation
uses normal startup error handling; a startup error must not silently restore
the old Session or strand ownership of either instance.

The expiring-ID condition aborts the switch request with an explicit error and
no registry/binding changes. It is not a supported multi-generation workload.
Do not terminate the MCP server process or add a retry queue.

### 4. Capture and release the actual instance

The request boundary validates the public ID, resolves the current instance
once, and records request ownership on that instance. Nested operations use the
supplied RequestContext/Session, never another lookup by the same ID.

Runtime release must refer to that captured instance, not whichever Session is
currently stored under its ID. Move unconditional request-finally retention out
of the completion path: initial promotion and explicit replacement are the only
ways to publish bound instances.

A switch returns its replacement explicitly. Its response formatting and
instruction processing use that replacement; the original request's lifetime
accounting still releases the outgoing instance. Other in-flight requests keep
their own original contexts unchanged.

Modern explicit IDs and retained legacy connection IDs use the same runtime
replacement operation. Do not mint, retire or reconnect the underlying FastMCP
session as part of a project switch.

### 5. Expiry finishes old work, then disposes of it

On entering expiring, the old Session is no longer a target for new requests,
configuration notifications or new recurring task scheduling. Stop further
subscriptions/timer firings for that instance without cancelling an already
executing operation merely because it can still save configuration.

Keep existing request and task/listener executions owned and tracked by their
Session/TaskManager until completion, including startup work already admitted.
Once those executions finish, dispose of the instance's listeners, tasks,
timers, queues, acknowledgement records and caches together and remove its
expiring entry. Use the Session and TaskManager's lifecycle APIs; do not make
runtime enumerate cache keys or reset individual project fields.

Existing operations may return to their original invocation and save the
original project's configuration through the shared ConfigManager. Expiry is
not a write prohibition. Those saves neither change the new Session's binding
nor re-register the old Session. Normal publication still reaches any active
Session legitimately using the exact configuration that was written.

No old caches, queued instructions, subscriptions or acknowledgements transfer
to the replacement. Work which finishes late references only its old Session.
Subsequent client replies are ordinary new requests and resolve the current
Session; there is no lookup in the expiring collection for request routing.

Run cleanup outside configuration locks and outside registry publication.
Disposal runs in runtime-owned workers after admitted work drains; request
completion schedules it without awaiting cleanup or propagating cleanup errors
into an already successful response. Runtime shutdown waits for those workers.
Idle expiry uses the same expiring collection and skips owners with a pending
expiring instance. Failed idle disposal blocks a new initial binding for that
owner until disposal succeeds.

Idle expiry must still protect executing requests. Runtime shutdown must
dispose of unbound, bound and expiring instances, attempting all cleanup even
if one instance fails. Cleanup failure must not silently make an incompletely
disposed instance eligible for another replacement.

### 6. Remove locks whose shared binding no longer exists

Keep ConfigManager's existing configuration coordination/image protection and
cross-process file locking. Old and new Sessions still share that file.

Registry publication and instance request-accounting changes are short,
non-awaiting operations on the event loop; they do not require another
per-Session transition lock. Asynchronous preparation is followed by an
identity recheck at publication.

Remove the in-place binding transition lock, lock-spanning pre-switch callbacks,
and cancellation-shielded child transitions that existed to mutate a shared
bound Session. An immutable per-instance root/configuration identity does not
need a lock to protect it from rebinding.

Remove switch-specific expected-current-project fences and cache/dispatch
generations used only to prevent old work from writing into a reused Session.
Do not mechanically delete protection that still serves shared configuration
or ordinary same-Session flag/cache invalidation. Configuration changes remain
normal updates within a Session; they do not automatically replace it.

### 7. Keep verification at the lifecycle boundary

Adapt existing behavioural tests to assert different Session objects under an
unchanged public ID, original-instance completion, fresh replacement state and
eventual disposal. Test the single expiring-ID rejection rather than supporting
arbitrary rapid switches.

The earlier isolation audit is diagnostic background, not eight automatically
accepted implementation workstreams. No per-cache hole-plugging programme,
late-reply protocol, arbitrary coverage target or broad concurrent-edit suite is
added to this change. Preserve useful existing selector, path and legacy
protocol tests; normal full-suite and pre-commit hygiene stays outside the
OpenSpec implementation task list.

## Alternatives Considered

- **Reset and rebind the same Session:** rejected because every old producer can
  retain access to the reused caches/queues and requires individual guards.
- **Add a separate project-lifetime container:** rejected because Session already
  owns that state; another abstraction adds indirection.
- **Replace Session and expire the old instance:** selected because old/new
  mutable state is separated by ordinary object ownership.

## Risks / Trade-offs

- [An old request republishes itself] -> runtime alone promotes/replaces bound
  instances; completion only releases its captured instance.
- [An old operation waits on a configuration write] -> allow it to finish against
  its original identity and never hold a configuration lock while draining it.
- [A second switch arrives before cleanup] -> reject it unchanged; retain one
  expiring entry rather than accommodating multiple historical instances.
- [Client submits follow-up data after a switch] -> resolve the current Session,
  as explicitly required; no historical-response support.
- [Replacement needs fresh runtime setup] -> transfer only connection metadata,
  reuse normal initial binding activation, and preserve one-time protocol logging.

## Migration Plan

This revises the implementation approach within `add-switch-roots` (UT-393).
Rework the existing uncommitted transition implementation and its lifecycle
tests; reuse compatible selector, URI, path and protocol-log changes.

The revised tasks are verified against this design, not the superseded
reset-in-place implementation. Their completion records the fresh-Session
lifecycle implementation and its behavioural regression tests.

No persisted data migration or new public ID is required. Deploy or roll back
by restarting the server normally; clients then establish fresh interactions.
Leave other OpenSpec changes and main specs untouched until implementation and
the normal specification-sync/archive workflow.
