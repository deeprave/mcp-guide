# Design

## Context

Guide currently trusts stdio and remote callers equally. Its project hash is a
client path disambiguator, not a remote identity or tenancy key. Authentication
therefore applies only to named operational capabilities, never project ownership.

## Goals / Non-Goals

**Goals:** optional remote provider lifecycle, opaque request authorisation,
deployment-neutral HTTP(S) support, stable result codes, and scope predicates.

**Non-Goals:** credentials, accounts, token parsing, scope interpretation,
automatic login redirects, project ACLs, or client filesystem authority.

## Decisions

### One selected provider, provider-owned configuration

`--auth-provider <provider>` is the only Guide authentication option. The
provider is loaded from the `mcp_guide.auth_providers` entry-point group and
obtains its own configuration from its deployment environment. Omission leaves
all existing access behaviour unchanged; stdio never constructs a provider. The
Python contract and access-mode boundary are recorded in ADR-014.

### Opaque request-level authorisation

Guide registers every protected tool, resource, or prompt with its required
`AuthScope` enum value. A provider receives ephemeral request evidence once and
returns `UserAuthorisation`: a set of enum scopes plus an optional opaque HTTPS
hand-off. Guide does not receive a principal, token, or provider policy
explanation. The provider may attach its hand-off when it returns no scope.
Guide never redirects an MCP request.

Missing or invalid authentication produces `not_authorised` (HTTP 401 semantics);
an authenticated caller without the required scope receives `forbidden` (HTTP
403 semantics). These are Guide Result codes within MCP responses, not changes
to HTTP transport statuses or authentication challenges. The authentication
handoff remains attached to the authentication-required response.

### Direct scope declarations and dynamic projection

Each protected operation declares `user` or `admin` directly. `admin` is the
unrestricted override and also satisfies user operations. A future change may
introduce a configurable capability model when it is needed.

`auth.active` means a provider is selected; `auth.authenticated`, `auth.user`,
and `auth.admin` are scope predicates rather than identity claims. When
inactive, `auth.active` is false while every scope predicate is true. The map
is built per request, never placed in the per-session template cache, and is
omitted when no session is supplied. With a provider active, authenticated state
means `user` or `admin`; future capability scopes alone do not establish it.

### Capability policy

`set_project`, `switch_project`, normal `send_file_content`, and
`update_documents` are unprotected. `send_file_content` requires `user` only
when validated arguments request SQLite ingestion. Cloning, permission-path
changes, and global feature mutation require `admin`; profiles, project flags,
and category/collection mutation require `user`.
Onboarding may inspect configuration and collect choices without authentication;
applying settings or marking onboarding as skipped requires `user`.

### Remote ingress

The remote handler starts/stops the selected provider. The provider receives
request evidence from either HTTP or HTTPS. Guide does not decide whether TLS
terminates directly or at a reverse proxy; that boundary and any header policy
are deployment responsibility.

## Risks / Trade-offs

- [Provider outage] → fail selected remote transport startup closed.
- [Policy drift] → keep the direct scope declaration adjacent to each protected
  operation until a configurable policy is required.
- [Cross-request identity leakage] → build `auth` template data per request.
- [Capabilities mistaken for tenancy] → document that tenancy is future work.

## Migration Plan

1. Release with no provider selected and unchanged access.
2. Deploy a provider through direct HTTPS or a TLS-terminating reverse proxy,
   and verify scope enforcement and hand-off.
3. Remove provider selection to roll back; Guide has no credentials to migrate.
