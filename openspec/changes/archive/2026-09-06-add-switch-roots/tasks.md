## 1. Runtime-owned Session lifecycle

- [x] 1.1 Reuse the ephemeral unbound and active bound collections, add a single expiring entry per validated owner, and restrict promotion/replacement to runtime; verify lifecycle tests cover unbound disposal, successful initial promotion and one-way bound-to-expiring ownership.
- [x] 1.2 Make request acquisition and release track the exact Session instance, remove unconditional request-finally retention, and keep active idle timestamps separate from old-instance completion; verify an old request finishing after replacement cannot restore its Session or release the new instance's request ownership.

## 2. Fresh-session project replacement

- [x] 2.1 Prepare a fresh Session with the target's immutable root/configuration identity and fresh caches, tasks, listeners and queues; transfer only public ID, client/agent connection metadata and establishment-log state; verify old/new mutable components are distinct and failed preparation leaves the active binding unchanged.
- [x] 2.2 Add runtime's non-awaiting expected-instance replacement operation and single expiring-ID guard; verify path-only and name-only selection replace the instance, an unchanged selection is a no-op without pending expiry, and any switch while the ID is expiring fails without changing either instance.
- [x] 2.3 Route switch_project through runtime replacement and use the returned Session explicitly for response formatting and initial-bound instruction delivery; verify the public ID is unchanged and old request accounting still releases the outgoing instance.
- [x] 2.4 Preserve the exactly-one-selector schema, rebind-project-root tool description, lexical relative/absolute and local percent-decoded file-URI handling, existing user-anchor errors and initial-only set_project contract; verify the existing argument/path/advertised-schema tests against the replacement path.

## 3. Expiring-session completion and disposal

- [x] 3.1 Stop new request admission, configuration notifications and recurring scheduling for an expiring Session while tracking its already-admitted request, listener and task executions through completion; verify a paused old callback cannot be routed to the replacement and a switch does not wait for its own request to finish.
- [x] 3.2 Allow admitted old work to finish configuration saves against its original project through the shared ConfigManager, without active-instance/key fences that reject expiry alone; verify the original configuration is saved, normal active-peer publication still works, and the replacement binding is untouched.
- [x] 3.3 Dispose of the old Session's owned resources after its admitted work drains, then remove its expiring entry; integrate unbound/idle/runtime-shutdown cleanup without holding configuration locks; verify final callback completion releases the entry, another switch is then permitted, and cleanup failure does not skip remaining instances or silently release the pending-expiry guard.

## 4. Simplify ownership and synchronisation

- [x] 4.1 Remove in-place rebinding, pre-switch cache-reset choreography, per-Session transition/binding protection needed only for rebinding, and shielded child transitions; retain ConfigManager coordination and file locking; verify immutable per-instance binding and a listener's configuration write without a switch-lock dependency.
- [x] 4.2 Remove switch-only project-key fences and cache/dispatch-generation checks made redundant by separate Session instances; retain ordinary flag/configuration invalidation and genuinely shared-resource protection; verify a delayed old cache/task completion affects only its old instance and ordinary flag toggles still refresh the active Session.

## 5. Public context, compatibility and documentation

- [x] 5.1 Preserve explicit Session propagation and modern/legacy ID validation, resolve all follow-up requests (including client replies) to the current bound instance, and avoid minting or retiring FastMCP IDs during replacement; verify modern and retained-legacy request round trips plus the switch response's replacement context.
- [x] 5.2 Preserve one-time negotiated-protocol/client establishment logging across internal Session replacement without logging public IDs or client paths; verify first establishment logs once and project replacement does not create another establishment log.
- [x] 5.3 Update user-facing session/root-switch documentation and ADR-012 to describe unbound -> bound -> expiring, stable public IDs, original-project completion and pending-expiry rejection; verify those documents agree with the revised delta specs and do not describe in-place reset, historical reply routing or a new client token.

Normal full-suite execution and pre-commit checks remain repository hygiene,
not additional implementation tasks. Reuse and adapt existing behavioural tests
rather than adding tests solely to raise coverage.
