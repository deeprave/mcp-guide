## ADDED Requirements

### Requirement: Explicit tool cache-policy metadata
The tool response adapter SHALL attach Guide cache-policy information to `_meta` only when the tool supplies an explicitly resolved valid policy.  It SHALL preserve existing non-cache result metadata independently.

The adapter SHALL NOT emit `io.modelcontextprotocol/cache-ttl-ms` or `io.modelcontextprotocol/cache-scope` on tool, prompt, or resource results.

#### Scenario: Explicitly cacheable tool result
- **WHEN** a tool supplies an explicitly resolved cache policy
- **THEN** the tool result `_meta` contains the Guide cache-policy information
- **AND** it does not contain either undocumented `io.modelcontextprotocol/cache-*` key

#### Scenario: Prompt without a policy
- **WHEN** a prompt response has no explicit cache policy
- **THEN** its existing result metadata is preserved
- **AND** it does not contain cache-policy metadata

#### Scenario: Resource adapter without a policy
- **WHEN** the resource adapter receives no explicit cache policy
- **THEN** it does not emit either undocumented `io.modelcontextprotocol/cache-*` key
