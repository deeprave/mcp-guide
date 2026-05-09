## ADDED Requirements

### Requirement: Alias-Implied Command URI Arguments

The guide:// command URI alias mechanism SHALL support aliases whose
frontmatter definitions include query strings whose parsed parameters are merged
into the canonical command invocation.

#### Scenario: Command URI alias lookup ignores query suffix
- **WHEN** a command defines an alias `project?verbose`
- **THEN** command URI alias matching SHALL resolve the user-facing alias as
  `project`
- **AND** the query suffix SHALL be used only for implied kwargs

#### Scenario: Alias URI implies kwargs
- **WHEN** a command defines an alias `project?verbose`
- **AND** the agent reads the alias form `guide://_project`
- **THEN** the normalized command invocation SHALL include `verbose=true`

#### Scenario: Canonical URI remains unchanged
- **WHEN** the agent reads `guide://_project/project`
- **THEN** the command URI SHALL resolve to the canonical project command
- **AND** it SHALL NOT depend on alias-implied kwargs

#### Scenario: Alias URI preserves explicit kwargs
- **WHEN** a command defines an alias `project?verbose`
- **AND** the agent reads `guide://_project?table=true`
- **THEN** the normalized command invocation SHALL include `verbose=true`
- **AND** it SHALL preserve `table=true`

#### Scenario: Generic behavior applies to any alias-bearing command
- **WHEN** any command alias contains a query string
- **THEN** guide:// alias resolution SHALL merge the parsed alias query
  parameters into the canonical command kwargs without command-specific rules

#### Scenario: Save-context URI implies write mode through handoff alias metadata
- **WHEN** the handoff command defines an alias `save-context?write`
- **AND** the agent reads `guide://_save-context/handoff.md`
- **THEN** the normalized command invocation SHALL resolve through the canonical
  handoff command
- **AND** it SHALL include `write=true`
- **AND** it SHALL preserve the target path `handoff.md`

#### Scenario: Restore-context URI implies read mode through handoff alias metadata
- **WHEN** the handoff command defines an alias `restore-context?read`
- **AND** the agent reads `guide://_restore-context/handoff.md`
- **THEN** the normalized command invocation SHALL resolve through the canonical
  handoff command
- **AND** it SHALL include `read=true`
- **AND** it SHALL preserve the target path `handoff.md`
