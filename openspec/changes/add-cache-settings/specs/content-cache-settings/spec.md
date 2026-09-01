## Purpose

Hosted content and explicitly opted-in deterministic responses need a precise, author-controlled cache policy that is safe by default and survives rendering and composition.

## ADDED Requirements

### Requirement: Hosted-document cache declaration
The system SHALL accept a `cache` frontmatter mapping on a hosted document with a positive integer `ttl_ms` and a `scope` of `private` or `public`.

Documents without a valid `cache` mapping SHALL have the no-cache policy.  A templated document SHALL be eligible for caching when its declared policy resolves to a cacheable policy; the presence of template expressions SHALL NOT override the declaration.

#### Scenario: Private document declaration
- **WHEN** a hosted document declares `cache: {ttl_ms: 60000, scope: private}`
- **THEN** the document's declared policy is private with a 60,000 millisecond lifetime

#### Scenario: Omitted declaration
- **WHEN** a hosted document has no `cache` frontmatter
- **THEN** the document's declared policy is no-cache

#### Scenario: Templated document declaration
- **WHEN** a templated hosted document declares a valid public cache policy
- **THEN** the declared public policy remains eligible for delivery after rendering

### Requirement: Cache-setting validation
The system SHALL reject cache settings with an invalid shape, non-positive lifetime, or unsupported scope as cacheable policies.  The affected content SHALL be delivered with the no-cache policy and the invalid declaration SHALL be diagnosable to the content author.

#### Scenario: Invalid scope
- **WHEN** a hosted document declares `cache.scope: shared`
- **THEN** its resolved policy is no-cache
- **AND** the invalid setting is reported as a validation diagnostic

#### Scenario: Non-positive lifetime
- **WHEN** a hosted document declares `cache.ttl_ms: 0`
- **THEN** its resolved policy is no-cache
- **AND** the invalid setting is reported as a validation diagnostic

### Requirement: Conservative composed-content resolution
The system SHALL resolve a cache policy for a content delivery from every hosted document that contributes rendered content, including partials.  A no-cache contributor SHALL make the delivery no-cache; otherwise the delivery SHALL use the shortest declared lifetime and `private` scope when any contributor is private.

#### Scenario: Mixed public and private contributors
- **WHEN** a content delivery combines a public 120,000 millisecond document and a private 60,000 millisecond partial
- **THEN** the resolved policy is private with a 60,000 millisecond lifetime

#### Scenario: Undeclared partial
- **WHEN** a cacheable document includes a partial with no cache declaration
- **THEN** the resolved delivery policy is no-cache

### Requirement: Explicit non-document response opt-in
The system SHALL permit a non-document response to carry cache policy only when its producing tool or resource explicitly declares a valid policy.  It SHALL NOT infer a policy solely from the response type, structured-data shape, or whether its content appears static.

#### Scenario: Explicit deterministic tool policy
- **WHEN** a tool explicitly declares a valid private cache policy for a deterministic response
- **THEN** the response carries that resolved policy

#### Scenario: Tool without a policy
- **WHEN** a tool returns a response without an explicit cache policy
- **THEN** the response carries no cache policy
