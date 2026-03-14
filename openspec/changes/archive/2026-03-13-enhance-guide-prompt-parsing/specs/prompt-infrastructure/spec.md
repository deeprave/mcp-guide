## ADDED Requirements

### Requirement: Space-Separated Flag Values
The command parser SHALL support space-separated flag values (`--flag value`) for flags declared in frontmatter `kwargs.argrequired`.

#### Scenario: Flag with equals syntax
- **WHEN** parsing `--tracking=GUIDE-177` where `tracking` is in `argrequired`
- **THEN** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** behavior is unchanged from current implementation

#### Scenario: Flag with space-separated syntax
- **WHEN** parsing `--tracking GUIDE-177` where `tracking` is in `argrequired`
- **THEN** parser SHALL consume next argument as the flag value
- **AND** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** `"GUIDE-177"` SHALL NOT appear in positional args

#### Scenario: Flag without value when required
- **WHEN** parsing `--tracking` where `tracking` is in `argrequired`
- **AND** no value follows (end of arguments or next token starts with `-`)
- **THEN** parser SHALL add error: `"Flag --tracking requires a value"`
- **AND** `kwargs["tracking"]` SHALL NOT be set

#### Scenario: Flag not in argrequired list
- **WHEN** parsing `--verbose` where `verbose` is NOT in `argrequired`
- **THEN** parser SHALL treat it as boolean flag
- **AND** `kwargs["verbose"]` SHALL equal `True`
- **AND** behavior is unchanged from current implementation

#### Scenario: Multiple required flags
- **WHEN** parsing `--tracking GUIDE-177 --issue fix-bug --verbose`
- **AND** `tracking` and `issue` are in `argrequired`
- **THEN** `kwargs["tracking"]` SHALL equal `"GUIDE-177"`
- **AND** `kwargs["issue"]` SHALL equal `"fix-bug"`
- **AND** `kwargs["verbose"]` SHALL equal `True`

#### Scenario: Required flag followed by another flag
- **WHEN** parsing `--tracking --verbose` where `tracking` is in `argrequired`
- **THEN** parser SHALL add error: `"Flag --tracking requires a value"`
- **AND** `kwargs["tracking"]` SHALL NOT be set
- **AND** `kwargs["verbose"]` SHALL equal `True`

### Requirement: Frontmatter-Driven Argument Requirements
The command parser SHALL accept `argrequired` list from frontmatter to determine which flags require values.

#### Scenario: Parser receives argrequired list
- **WHEN** `parse_command_arguments()` is called with `argrequired=["tracking", "issue"]`
- **THEN** parser SHALL use this list to determine flag value requirements
- **AND** flags in list SHALL consume next argument as value when no `=` present

#### Scenario: Parser without argrequired list
- **WHEN** `parse_command_arguments()` is called without `argrequired` parameter
- **THEN** parser SHALL use current behavior for all flags
- **AND** backward compatibility is maintained

#### Scenario: Empty argrequired list
- **WHEN** `parse_command_arguments()` is called with `argrequired=[]`
- **THEN** parser SHALL treat all flags as boolean
- **AND** behavior matches current implementation
