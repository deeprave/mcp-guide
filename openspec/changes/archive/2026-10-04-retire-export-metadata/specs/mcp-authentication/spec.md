# Spec Delta

## REMOVED Requirements

### Requirement: Direct protected-operation scopes

**Reason**: Replace the scope contract without its retired export-metadata
scenario. Preserve registration and unprotected-operation behaviour in the
replacement requirement below; no archived change is rewritten.

**Migration**: Keep existing user/admin declarations for mutating operations.
Stateless export has no mutation-based scope gate but retains configured
write-path validation.

## ADDED Requirements

### Requirement: Direct operation scope enforcement
Each protected tool, resource, or prompt SHALL declare its required `AuthScope`
string-enum value directly. The initial values are `user` and `admin`; `admin`
SHALL satisfy every protected-operation scope. A later change MAY introduce
additional scopes or configurable policy.

Operations without a declared scope SHALL retain existing access behaviour.
The classification SHALL apply only while a provider-backed remote policy is
active and SHALL be enforced after argument validation and before an operation
has an effect. Later protected resources and prompts SHALL use this same
boundary.

#### Scenario: A protected operation is registered
- **GIVEN** a tool, resource, or prompt is protected
- **WHEN** a tool, resource, or prompt is protected
- **THEN** its registration SHALL identify its required scope enum value
- **AND** that scope requirement SHALL be applied at the request boundary

#### Scenario: An unprotected operation is called with provider active
- **GIVEN** provider-backed remote policy is active
- **WHEN** a caller invokes an operation without a declared protected scope
- **THEN** the system SHALL preserve that operation's existing access and
  result behaviour

#### Scenario: Stateless export with provider active
- **GIVEN** an authentication provider is active
- **WHEN** a caller requests a non-mutating `export_content` operation
- **THEN** no mutation-based `user` scope SHALL be required for that export
- **AND** its configured write-path validation SHALL still apply
- **AND** project configuration and permissions SHALL remain unchanged
