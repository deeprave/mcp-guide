## ADDED Requirements

### Requirement: Client-aware root identity
RequestContext root identity SHALL use the applicable client resolution policy.
Unverified/disabled paths SHALL remain lexical without resolving server symlinks;
verified shared stdio paths MAY use ordinary server filesystem resolution.

#### Scenario: Unshared server-visible symlink
- **WHEN** distinct absolute client roots include a symlink visible only to the server and sharing is unverified or disabled
- **THEN** their lexical root identities and hashes SHALL remain distinct

#### Scenario: Verified shared root
- **WHEN** verified stdio resolves a client root
- **THEN** its identity SHALL match the shared filesystem resolution result

#### Scenario: Verification after initial binding
- **WHEN** sharing becomes verified after a root was already bound lexically
- **THEN** that existing binding and its configuration identity SHALL remain unchanged
- **AND** subsequent root selections SHALL use the verified resolution policy
