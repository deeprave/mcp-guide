# Proposal

## Why

Guide has a pluggable authentication boundary but needs an adapter that can use
the reference provider service now maintained outside this repository. The
adapter proves that boundary without turning Guide into an identity provider or
duplicating the provider service's accounts, credentials, lifecycle, or
administration responsibilities.

## What Changes

- Add an optional provider module, selected through Guide's existing provider
  entry-point mechanism, that connects to the external reference provider
  service over its configured TLS endpoint.
- Only when a protected remote operation requires an authentication decision,
  forward the ephemeral bearer evidence needed by the service's authentication
  endpoint. Convert its limited decision into Guide's `UserAuthorisation`
  scopes, discarding account identity and every other provider detail. Remote
  rendering without such a decision exposes fail-closed access predicates.
- Define and test the service-adapter contract: request authentication,
  response validation, `user` and `admin` mapping, provider errors, TLS
  connection failure, and request-local credential handling.
- Document installation, external service configuration, TLS trust, remote
  transport selection, and the separation of Guide from the provider service.

## Capabilities

### New Capabilities

- `reference-auth-provider`: optional Guide adapter for the independently
  operated reference authentication-provider service.

### Modified Capabilities

- `mcp-authentication`: load and start a selected provider at the first
  protected operation, rather than at remote transport startup; provider
  configuration or startup failure affects that operation only. Remote template
  access predicates are fail-closed while request evidence is bound but no
  provider decision exists.
- `template-context`: represent remote request evidence without a provider
  decision as active but unauthenticated, rather than as inactive with
  unrestricted predicates.

## Impact

- Adds the adapter's optional HTTP client dependency, entry-point metadata,
  provider-owned configuration, tests, and operator documentation.
- Depends on the provider contract introduced by `add-mcp-authentication` and
  on the external service's versioned authentication endpoint.
- Does not add an identity-provider application, database, credential store,
account-management command, provider process lifecycle, signing keys, login
pages, or token issuance to Guide.
- Is opt-in and does not alter stdio or remote behaviour when no authentication
  provider is selected.
