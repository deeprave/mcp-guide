## ADDED Requirements

### Requirement: Client-aware inherited-PWD bootstrap
Inherited-PWD bootstrap SHALL require verified shared stdio state as well as its
existing explicit opt-in. It SHALL NOT use server PWD while verification is
pending, failed or disabled.

#### Scenario: Unverified or HTTP inherited PWD
- **WHEN** bootstrap is enabled but shared stdio access is not verified
- **THEN** the interaction SHALL remain unbound until given an absolute client root

#### Scenario: Verified inherited PWD
- **WHEN** stdio sharing is verified and inherited-PWD bootstrap is explicitly enabled
- **THEN** bootstrap MAY bind through LazyPath.client_resolve()
