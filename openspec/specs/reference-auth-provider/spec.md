# reference-auth-provider Specification

## Purpose

Provide an optional Guide adapter for the independently operated reference
authentication-provider service, without making Guide implement or operate that
service.

## Requirements

### Requirement: Optional reference provider-service adapter

The distribution SHALL expose an optional authentication-provider module through
Guide's authentication-provider entry-point mechanism. Selecting the module
SHALL require its optional dependency and provider-owned configuration; it SHALL
not enable authentication by default.

#### Scenario: Service adapter is deliberately selected
- **WHEN** an administrator starts a remote Guide transport with the reference
  provider-service adapter selected and valid provider configuration
- **THEN** Guide retains the adapter selection without loading or contacting it
  during transport startup
- **AND WHEN** a protected operation requires an authentication decision
- **THEN** Guide loads and starts the adapter
- **AND** an otherwise unchanged installation without the selection does not
  load the adapter

### Requirement: External service ownership and trust configuration

The module SHALL connect only to a pre-existing external reference provider
service. Guide SHALL NOT start, stop, supervise, or administer that service.

#### Scenario: External service is unavailable at transport startup
- **GIVEN** the reference provider-service adapter is selected
- **AND** its configured service is unavailable
- **WHEN** Guide starts the remote transport
- **THEN** the remote transport SHALL start without contacting the external
  service
- **AND** Guide SHALL NOT attempt to start or otherwise manage the service

### Requirement: Provider endpoint trust configuration

Provider-specific configuration SHALL identify the service endpoint through the
provider-owned `AG_ADDRESS` setting without adding a Guide provider-config CLI
argument. The adapter SHALL build its TLS context from the operating-system
trust store, SHALL NOT accept a Guide-specific CA bundle, and SHALL require
certificate validation for its service connection.

#### Scenario: Provider uses a private certificate authority
- **WHEN** an operator configures a provider endpoint issued by a private
  certificate authority
- **THEN** Guide SHALL use the operating-system trust store to validate it
- **AND** the operator SHALL not configure a Guide-specific CA bundle

### Requirement: Lazy protected-operation decision

Provider start SHALL NOT contact the external service or prevent the selected
remote transport from serving unprotected operations. Failure to connect to the
configured service while obtaining an authentication decision SHALL prevent the
requested protected operation from being performed. An operation without an
authentication requirement SHALL NOT contact the provider.

#### Scenario: An unprotected operation is dispatched
- **GIVEN** the reference provider-service adapter is selected
- **WHEN** a caller invokes an unprotected operation
- **THEN** Guide SHALL dispatch it without contacting the provider service

### Requirement: Bounded provider failure handling

The adapter SHALL bound each connection and authentication decision to five
seconds. A timeout after the connection phase SHALL fail closed with a safe
response-timeout diagnostic. A connection timeout, TLS failure, or other
connection failure SHALL fail closed with a safe connection-failure diagnostic.
Neither diagnostic SHALL contain bearer evidence or a provider response body.

#### Scenario: Provider connection fails for a protected operation
- **WHEN** a protected operation cannot connect to the provider service
- **THEN** Guide SHALL return an `authentication_unavailable` Result with the
  safe connection-failure diagnostic
- **AND** it SHALL NOT invoke the protected operation

### Requirement: Fail-closed remote template projection

When a provider-backed remote request has bound evidence but no provider
decision, template access predicates SHALL be active and fail closed:
`authenticated`, `user`, and `admin` SHALL all be false. This projection SHALL
NOT require a provider call.

#### Scenario: Template rendering has no provider decision
- **GIVEN** a provider-backed remote request with bound evidence
- **WHEN** a session-bound template renders before a provider decision exists
- **THEN** all scope predicates SHALL be false without contacting the provider

### Requirement: Narrow external authentication decision

For each remote request, the adapter SHALL send only the request's ephemeral
bearer evidence to the provider service's versioned Guide authentication
endpoint over a TLS-verified connection. It SHALL accept only the limited
authentication decision required by Guide: recognised Guide scopes. It SHALL
discard account identifiers and every other provider response field before
returning `UserAuthorisation` to Guide.

#### Scenario: Valid bearer supplies user access
- **WHEN** a remote caller presents bearer evidence accepted by the external
  provider service with no recognised administrative scope
- **THEN** the adapter returns `UserAuthorisation` containing `user`
- **AND** Guide does not receive the bearer, account identifier, or other
  provider response data

### Requirement: Provider-decision scope mapping

A successful decision SHALL grant `AuthScope.USER`. A decision containing the
recognised `admin` scope SHALL additionally grant `AuthScope.ADMIN`. The
adapter SHALL reject unknown, duplicate, malformed, or contradictory scope
values.

#### Scenario: Valid bearer supplies administrative access
- **WHEN** a remote caller presents bearer evidence accepted by the external
  provider service with the recognised `admin` scope
- **THEN** the adapter returns `UserAuthorisation` containing `user` and
  `admin`
- **AND** Guide applies its existing admin-satisfies-user rule

### Requirement: Provider evidence and result privacy

The adapter SHALL not parse token formats, retain bearer evidence after the
request, or expose bearer data, account identity, response bodies, provider
objects, or service configuration to Guide handlers or templates.

#### Scenario: Provider returns account metadata
- **WHEN** the provider response contains an account identifier or other
  provider-private metadata alongside its scope decision
- **THEN** the adapter SHALL discard that metadata before returning
  `UserAuthorisation` to Guide

#### Scenario: Missing or rejected bearer requires authentication
- **WHEN** a remote caller invokes a protected operation without bearer
  evidence accepted by the external provider service
- **THEN** the adapter returns unauthenticated `UserAuthorisation`
- **AND** Guide returns its existing `not_authorised` result

### Requirement: Service failures and invalid decisions fail closed

The adapter SHALL fail closed when the service response is malformed, contains
an unknown or invalid scope, uses an unexpected content type, cannot be reached
over verified TLS, or returns an unexpected service failure. It SHALL use the
existing provider-failure behaviour and SHALL NOT reuse a prior request's
authorisation or permit the protected operation. Diagnostics SHALL NOT include
bearer values, authorisation headers, or provider response bodies.

#### Scenario: Provider response has an unknown scope
- **WHEN** the configured provider service returns a successful response with
  an unknown scope value
- **THEN** the adapter SHALL reject that response as a provider failure
- **AND** Guide SHALL not perform the protected operation

#### Scenario: Provider TLS verification fails
- **WHEN** the configured provider service certificate cannot be validated
- **THEN** the adapter SHALL fail closed
- **AND** it SHALL not retry through an unverified connection
