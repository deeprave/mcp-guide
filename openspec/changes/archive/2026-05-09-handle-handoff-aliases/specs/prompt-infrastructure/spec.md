## ADDED Requirements

### Requirement: Alias-Implied Command Arguments

Command frontmatter aliases SHALL support query strings whose parsed parameters
are merged into the canonical command kwargs when the alias is invoked.

#### Scenario: Alias implies boolean kwargs
- **WHEN** a command defines an alias `project?verbose`
- **THEN** invoking `:project` SHALL normalize to the canonical command with
  `kwargs["verbose"] = True`

#### Scenario: Explicit kwargs are preserved alongside alias kwargs
- **WHEN** a command defines an alias `project?verbose`
- **AND** the user invokes `:project --table`
- **THEN** the normalized command SHALL include `kwargs["verbose"] = True`
- **AND** it SHALL preserve `kwargs["table"] = True`

#### Scenario: Alias name matching ignores query suffix
- **WHEN** a command defines an alias `project?verbose`
- **THEN** command lookup and alias matching SHALL resolve the user-facing alias
  name as `project`
- **AND** the query suffix SHALL be used only for implied kwargs

#### Scenario: Alias query values use normal query parsing rules
- **WHEN** a command defines an alias `project?verbose=true&table=false`
- **THEN** the implied kwargs SHALL be parsed using the same normalization rules
  as other command query parameters
- **AND** the normalized invocation SHALL include `kwargs["verbose"] = True`
- **AND** the normalized invocation SHALL include `kwargs["table"] = False`

#### Scenario: Generic behavior is not command-specific
- **WHEN** any command defines an alias with query parameters
- **THEN** alias query propagation SHALL be available without adding
  command-specific parsing or resolution rules

#### Scenario: Save-context alias implies handoff write mode
- **WHEN** the handoff command defines an alias `save-context?write`
- **AND** the user invokes `:save-context handoff.md`
- **THEN** the command SHALL normalize to the canonical handoff command
- **AND** the normalized invocation SHALL include `kwargs["write"] = True`
- **AND** the target path SHALL remain `handoff.md`

#### Scenario: Restore-context alias implies handoff read mode
- **WHEN** the handoff command defines an alias `restore-context?read`
- **AND** the user invokes `:restore-context handoff.md`
- **THEN** the command SHALL normalize to the canonical handoff command
- **AND** the normalized invocation SHALL include `kwargs["read"] = True`
- **AND** the target path SHALL remain `handoff.md`
