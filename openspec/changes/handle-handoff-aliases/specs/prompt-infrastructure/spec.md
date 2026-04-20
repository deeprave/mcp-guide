## ADDED Requirements

### Requirement: Alias-Implied Command Arguments

Command frontmatter aliases SHALL support query-style boolean flags that are
merged into the canonical command kwargs when the alias is invoked.

#### Scenario: Alias implies boolean kwargs
- **WHEN** a command defines an alias `save-context?write`
- **THEN** invoking `:save-context handoff.md` SHALL normalize to the canonical
  command with `kwargs["write"] = True`

#### Scenario: Explicit kwargs are preserved alongside alias kwargs
- **WHEN** a command defines an alias `save-context?write`
- **AND** the user invokes `:save-context handoff.md --verbose`
- **THEN** the normalized command SHALL include `kwargs["write"] = True`
- **AND** it SHALL preserve `kwargs["verbose"] = True`

#### Scenario: Alias name matching ignores query suffix
- **WHEN** a command defines an alias `restore-context?read`
- **THEN** command lookup and alias matching SHALL resolve the user-facing alias
  name as `restore-context`
- **AND** the query suffix SHALL be used only for implied kwargs

### Requirement: Handoff Command Aliases

The command parser SHALL support `:save-context` and `:restore-context` as
intent-specific aliases for the existing handoff command flow.

The `save-context` alias SHALL imply handoff write mode.
The `restore-context` alias SHALL imply handoff read mode.

Both aliases SHALL continue to require a concrete target path argument.

#### Scenario: Save-context alias implies write mode
- **WHEN** the user invokes `:save-context handoff.md`
- **THEN** the command flow SHALL be normalized to the canonical handoff command
- **AND** the effective handoff mode SHALL be write
- **AND** the target path SHALL be `handoff.md`

#### Scenario: Restore-context alias implies read mode
- **WHEN** the user invokes `:restore-context handoff.md`
- **THEN** the command flow SHALL be normalized to the canonical handoff command
- **AND** the effective handoff mode SHALL be read
- **AND** the target path SHALL be `handoff.md`

#### Scenario: Alias without path is rejected
- **WHEN** the user invokes `:save-context` or `:restore-context` without a
  target path
- **THEN** the command parser SHALL return an error indicating that a handoff
  file path is required

#### Scenario: Conflicting explicit mode is rejected
- **WHEN** the user invokes `:save-context handoff.md --read`
- **THEN** the normalized command SHALL include both `read` and `write`
- **AND** the canonical handoff validation SHALL return an error for the invalid
  mode combination
- **AND** the handoff command SHALL NOT execute

#### Scenario: Matching explicit mode remains valid
- **WHEN** the user invokes `:restore-context handoff.md --read`
- **THEN** the normalized command SHALL preserve `kwargs["read"] = True`
- **AND** the effective handoff mode SHALL remain read
