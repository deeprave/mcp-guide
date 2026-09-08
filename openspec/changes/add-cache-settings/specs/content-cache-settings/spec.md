## Purpose

Hosted content and explicitly opted-in deterministic responses need a precise, author-controlled cache policy that is safe by default and survives rendering and composition.

## ADDED Requirements

### Requirement: Hosted-document cache declaration
The system SHALL accept a concise `cache` frontmatter declaration containing comma-separated symbolic tokens. The valid lifetime tokens are `long` (24 hours), `medium` (15 minutes), and `short` (2 minutes); the valid scope tokens are `private` and `public`. `shared` SHALL be accepted as an alias for `public`.

Documents declaring `none` or `no-cache`, and documents without a valid declaration other than ordinary non-template Markdown, SHALL have the no-cache policy. Ordinary non-template Markdown without a `cache` key SHALL resolve to the `long, public` policy. A declaration without scope SHALL default to `public`; one without lifetime SHALL default to `medium`. A templated document SHALL be eligible for caching when its declared policy resolves to a cacheable policy; the presence of template expressions SHALL NOT override the declaration.

#### Scenario: Private document declaration
- **WHEN** a hosted document declares `cache: medium, private`
- **THEN** the document's declared policy is private with a 15-minute lifetime

#### Scenario: Public scope shorthand
- **WHEN** a hosted document declares `cache: public`
- **THEN** the document's declared policy is public with a 15-minute lifetime

#### Scenario: Omitted declaration on ordinary Markdown
- **WHEN** a non-template Markdown hosted document has no `cache` frontmatter
- **THEN** the document's resolved policy is public with a 24-hour lifetime

#### Scenario: Omitted declaration on a rendered document
- **WHEN** a rendered hosted document has no `cache` frontmatter
- **THEN** the document's resolved policy is no-cache

#### Scenario: Shared scope alias
- **WHEN** a hosted document declares `cache: medium, shared`
- **THEN** the document's declared policy is public with a 15-minute lifetime

#### Scenario: Templated document declaration
- **WHEN** a templated hosted document declares a valid public cache policy
- **THEN** the declared public policy remains eligible for delivery after rendering

### Requirement: Bundled-document policy audit
The system SHALL audit every bundled template under `src/mcp_guide/templates` and add a cache declaration to each cacheable non-command document.  Static documents SHALL use public scope by default.  Documents that depend on flags, settings, `requires-*` directives, or conditional rendering based on those inputs SHALL use private scope.  Command templates and command-backed output SHALL remain no-cache.

#### Scenario: Static bundled policy
- **WHEN** an audited static bundled document is rendered through the common template path without consuming dynamic context
- **THEN** it has an explicit public cache declaration

#### Scenario: Flag-dependent bundled policy
- **WHEN** an audited bundled document changes output according to flags or settings
- **THEN** it has an explicit private cache declaration with a medium or short lifetime

### Requirement: Cache-setting validation
The system SHALL reject cache settings with an invalid shape, duplicate token, or unsupported lifetime or scope as cacheable policies.  The affected content SHALL be delivered with the no-cache policy and the invalid declaration SHALL be diagnosable to the content author.

#### Scenario: Unsupported scope
- **WHEN** a hosted document declares `cache: medium, protected`
- **THEN** its resolved policy is no-cache
- **AND** the invalid setting is reported as a validation diagnostic

#### Scenario: Invalid lifetime
- **WHEN** a hosted document declares `cache: immediate`
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

### Requirement: Document-only cache delivery in this change
The cache-policy carrier and response adapter SHALL accept an explicitly resolved policy from any response producer. This change SHALL attach cache policy only to document-delivery operations. Commands, prompts, command URIs, and non-document tools SHALL carry no cache policy unless a later change explicitly opts them in.

When document content is delivered with MIME formatting, every MIME document part SHALL include its own `Cache-Control` header. A cacheable part SHALL express its resolved scope and TTL in seconds; a no-cache part SHALL use `Cache-Control: no-cache`. Part headers SHALL use each file's own resolved policy, independently of the conservative aggregate policy attached to the overall response.

#### Scenario: Mixed-policy multipart content
- **WHEN** MIME-formatted content contains one `cache: long` document and one undeclared document
- **THEN** the cacheable part has `Cache-Control: public, max-age=86400`
- **AND** the undeclared part has `Cache-Control: no-cache`
- **AND** the overall response has no cache policy

#### Scenario: Command delivery
- **WHEN** a command template is rendered through a prompt or command URI
- **THEN** its response carries no cache policy
