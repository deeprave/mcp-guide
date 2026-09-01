## ADDED Requirements

### Requirement: Resource cache-policy metadata
The `guide://` resource handler SHALL attach the resolved Guide cache policy to the successful resource result's `_meta` information.  A resource with no resolved policy SHALL not advertise a cache policy.

The metadata SHALL describe the policy as Guide-specific information and SHALL NOT use undocumented `io.modelcontextprotocol/cache-*` keys as a substitute for protocol cache support.

#### Scenario: Cacheable hosted resource
- **WHEN** a `guide://` resource resolves to cacheable hosted content
- **THEN** its result `_meta` contains the resolved Guide cache policy

#### Scenario: Default resource policy
- **WHEN** a `guide://` resource resolves to content without a cache declaration
- **THEN** its result does not advertise a cache policy
