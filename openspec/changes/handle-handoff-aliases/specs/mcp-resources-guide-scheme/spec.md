## ADDED Requirements

### Requirement: Alias-Implied Command URI Arguments

The guide:// command URI alias mechanism SHALL support aliases whose frontmatter
definitions include query-style implied kwargs.

#### Scenario: Command URI alias lookup ignores query suffix
- **WHEN** a command defines an alias `_save-context?write`
- **THEN** command URI alias matching SHALL resolve the user-facing alias as
  `_save-context`
- **AND** the query suffix SHALL be used only for implied kwargs

#### Scenario: Alias URI merges implied and explicit kwargs
- **WHEN** a command defines an alias `_restore-context?read`
- **AND** the agent reads `guide://_restore-context/handoff.md?verbose=true`
- **THEN** the normalized command invocation SHALL include `read=true`
- **AND** it SHALL preserve `verbose=true`

### Requirement: Handoff Command URI Aliases

The guide:// command URI scheme SHALL support `_save-context` and
`_restore-context` as aliases for the existing handoff command behavior.

The `_save-context` alias SHALL imply handoff write mode.
The `_restore-context` alias SHALL imply handoff read mode.

Both aliases SHALL continue to require a concrete target path in the URI path
segments.

#### Scenario: Save-context URI implies write mode
- **WHEN** the agent reads `guide://_save-context/handoff.md`
- **THEN** the command URI SHALL be normalized to the canonical handoff command
- **AND** the effective handoff mode SHALL be write
- **AND** the target path SHALL be `handoff.md`

#### Scenario: Restore-context URI implies read mode
- **WHEN** the agent reads `guide://_restore-context/handoff.md`
- **THEN** the command URI SHALL be normalized to the canonical handoff command
- **AND** the effective handoff mode SHALL be read
- **AND** the target path SHALL be `handoff.md`

#### Scenario: Alias URI without path is rejected
- **WHEN** the agent reads `guide://_save-context`
- **THEN** the command handler SHALL return an error indicating that a handoff
  file path is required

#### Scenario: Conflicting query mode is rejected
- **WHEN** the agent reads `guide://_restore-context/handoff.md?write=true`
- **THEN** the normalized command SHALL include both `read` and `write`
- **AND** the canonical handoff validation SHALL return an error for the invalid
  mode combination
- **AND** the handoff command SHALL NOT execute

#### Scenario: Matching query mode remains valid
- **WHEN** the agent reads `guide://_save-context/handoff.md?write=true`
- **THEN** the normalized command SHALL preserve `write=true`
- **AND** the effective handoff mode SHALL remain write
