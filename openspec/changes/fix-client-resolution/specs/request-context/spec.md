## ADDED Requirements

### Requirement: Lexical client root identity
Request-context root identity SHALL preserve the lexical path declared by the
client after applicable client-path normalisation. It SHALL not collapse distinct
client roots because the Guide host can resolve one or more server-visible
symlinks.

#### Scenario: Server-visible client-path symlink
- **WHEN** two bound client roots have distinct lexical paths but one is a symlink on the Guide host
- **THEN** RequestContext SHALL expose distinct root identities and configuration hashes for the two paths
