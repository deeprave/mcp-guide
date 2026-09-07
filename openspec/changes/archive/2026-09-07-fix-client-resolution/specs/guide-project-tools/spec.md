## ADDED Requirements

### Requirement: Client-aware project root paths
Project binding and switching SHALL use LazyPath.client_resolve() after local
file-URI decoding. HTTP/HTTPS and unverified/failed stdio SHALL require absolute
client paths and SHALL reject relative, user-anchored and variable-bearing input.
Verified stdio SHALL permit shorthand and root-relative switching.
Initial binding SHALL require an absolute path after permitted user/environment
expansion, before filesystem resolution. It SHALL NOT use server CWD to make
relative initial input absolute. Absolute paths containing `..` SHALL be normalised,
not rejected merely for containing parent components.

#### Scenario: Relative initial root after verification
- **WHEN** verified stdio receives a relative initial root, including a variable that expands to a relative path
- **THEN** it SHALL reject the input and request an absolute client path

#### Scenario: Absolute root with parent components
- **WHEN** initial binding receives an absolute path containing `..`
- **THEN** it SHALL normalise it under the applicable client policy before binding

#### Scenario: Initial absolute root
- **WHEN** unverified stdio receives a valid absolute project root
- **THEN** it SHALL bind lexically and initiate one-shot verification

#### Scenario: Local file URI
- **WHEN** a project root uses a local percent-encoded file URI
- **THEN** its decoded path SHALL be checked against the client resolution policy

#### Scenario: Disabled shorthand
- **WHEN** HTTP/HTTPS or unverified stdio receives shorthand
- **THEN** it SHALL return invalid-path guidance requesting an absolute client path

#### Scenario: Verified root-relative switch
- **WHEN** verified stdio supplies a relative switch path
- **THEN** it SHALL resolve against the current bound root
