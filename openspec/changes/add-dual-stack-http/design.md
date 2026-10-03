# Design

## Context

See [proposal.md](proposal.md) for the motivation and exposure change. Guide
currently passes its parsed host and port to Uvicorn. Uvicorn's normal asyncio
listener creation explicitly enables `IPV6_V6ONLY`, so `[::]` does not accept
IPv4 connections even when the operating system supports dual-stack sockets.

`localhost` is different: hostname resolution can produce `127.0.0.1` and
`::1`, and the server can bind separate loopback listeners. IPv4 literals and
specific IPv6 addresses also have useful, existing address-specific semantics.

The pending `migrate-hypercorn-asgi` proposal replaces Guide's ASGI server.
This change defines listener behaviour, not a requirement to retain Uvicorn.

## Goals / Non-Goals

**Goals:**

- Make an explicit `[::]` bind accept both families predictably.
- Keep socket ownership within the existing HTTP transport lifecycle.
- Reuse one application and the existing TLS, authentication and admission
  layers rather than duplicating server instances.

**Non-Goals:**

- A new CLI flag, multiple endpoint syntax, configurable address-family policy
  or a general-purpose server abstraction.
- Making authentication mandatory, managing proxy policy, or changing hostname
  resolution and localhost defaults.
- Implementing the Hypercorn migration as part of this change.

## Decisions

### The explicit IPv6 wildcard requests dual-stack listening

Apply the new behaviour only when the parsed host is `::`. Leave `localhost`,
`0.0.0.0`, hostnames and specific IPv6 addresses on their existing binding path.
This makes the transport URL sufficient configuration without another flag.

The alternative of making `0.0.0.0` mean both families would change an IPv4
address's meaning. Automatically enabling wildcard access for hostless URLs
would undermine the agreed localhost default. Neither is needed.

### Configure the socket explicitly rather than relying on OS defaults

For the current Uvicorn backend, check `socket.has_dualstack_ipv6()` and create
the listener with `socket.create_server(("::", port), family=socket.AF_INET6,
dualstack_ipv6=True)`. Pass that listener to `Server.serve(sockets=[listener])`.
This retains the socket's explicit dual-stack setting instead of allowing
asyncio to create an IPv6-only socket. TLS remains configured on the ASGI server;
the raw listener is not independently TLS-wrapped.

If Hypercorn migration lands first, use its supported listener configuration
or socket integration to provide the same explicit dual-stack behaviour and
cleanup contract. Do not retain Uvicorn or introduce an interchangeable backend
layer solely for this change. Reconcile the overlapping transport work before
implementation.

A two-listener fallback is not included. If the platform cannot provide the
requested dual-stack listener, report startup failure instead of adding a
second lifecycle or silently narrowing the endpoint.

### Keep ownership and protection in the existing transport

The transport owns the listener from creation until shutdown. Close it on
failed startup, cancellation and normal shutdown, using the existing common
cleanup path rather than a separate provider lifecycle. Preserve the currently
configured backlog and serving behaviour when supplying a pre-bound socket.

IPv4 and IPv6 requests enter the same ASGI application, including provider
authentication and rate limiting. No scope, session or tool policy changes are
required. IPv4 peers may be represented as IPv4-mapped IPv6 addresses; do not
introduce client-address policy in this change.

## Risks / Trade-offs

- [An existing `[::]` deployment gains IPv4 exposure] → Mark the change as
  breaking and document that IPv6-only deployments must review their bind.
- [Platform support varies] → Detect unsupported dual-stack sockets, fail
  clearly, and skip only real dual-stack integration tests on unsupported hosts.
- [Pre-binding leaks a socket after failure] → Exercise startup failure,
  cancellation and shutdown, and verify that the bind can be reused afterwards.
- [ASGI migration overlaps this work] → Keep the specification backend-neutral
  and implement against the actual backend present at that time.

## Migration Plan

1. Resolve ordering with `migrate-hypercorn-asgi` and add behavioural tests.
2. Implement explicit dual-stack binding in the HTTP transport.
3. Document endpoint examples and the `[::]` exposure change.
4. Run focused transport tests, the full suite and strict OpenSpec validation.

Rollback restores the prior listener creation path and IPv6-only wildcard
behaviour. No stored configuration or document migration is required.
