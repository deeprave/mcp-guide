## Purpose

Allow an agent to export one explicitly named, rendered Guide skill package into
the current project using local skill-directory conventions without introducing
a server-side filesystem writer.

## ADDED Requirements

### Requirement: Project-scoped skill export command

The system SHALL provide a rendered `skills/export` command that directs the
agent to export a Guide skill only into the active bound project's filesystem.
The command SHALL be addressable through the normal command surfaces, including
`guide://_skills/export/<skill-name>?force=true`.
It SHALL render its help and execution requirements from the active session's
available Guide skills and parsed command arguments.

#### Scenario: Export from a command URI
- **WHEN** an agent reads `guide://_skills/export/workflow-review`
- **THEN** the command SHALL identify `workflow-review` as the named skill
- **AND** SHALL direct the agent to obtain and write its rendered package beneath `.agents/skills`

#### Scenario: Export is limited to the current project
- **WHEN** an agent invokes the command while a project is bound
- **THEN** the command SHALL direct all export paths to be resolved beneath that project root
- **AND** SHALL NOT direct the agent to write a global, server-owned, another project's, or alternative local skill directory

### Requirement: Canonical export location

The command SHALL export a named skill only to
`.agents/skills/<skill-name>/SKILL.md`. It SHALL NOT accept or present a
destination argument or an alternative export location.

#### Scenario: Use the canonical location
- **WHEN** an agent exports a named skill
- **THEN** the command SHALL direct it to create only
  `.agents/skills/<skill-name>/SKILL.md` beneath the bound project root

### Requirement: Single-skill selection and replacement

The command SHALL accept one positional public skill name. When the name is
omitted, it SHALL offer the active session's available skills for one selection.
It SHALL refuse to overwrite an existing canonical export unless its `force`
keyword is true after the user has explicitly requested replacement.

#### Scenario: Select a named skill
- **WHEN** an agent invokes `skills/export/workflow-review`
- **THEN** the command SHALL identify `workflow-review` for export

#### Scenario: Select a skill interactively
- **WHEN** the skill name is omitted and the client provides a native picker
- **THEN** the command SHALL direct the agent to present every available Guide skill as a selectable option
- **AND** SHALL use the user's single selection for export

#### Scenario: Use a non-interactive fallback
- **WHEN** a skill selection is required but the client does not provide a native picker
- **THEN** the command SHALL direct the agent to present the same choices in a clear textual form
- **AND** SHALL wait for the user's answer before exporting

#### Scenario: Refuse a pre-existing export
- **WHEN** `.agents/skills/<skill-name>` already exists and `force` is absent or false
- **THEN** the command SHALL report the existing entry
- **AND** SHALL NOT replace it

#### Scenario: Replace an existing export
- **WHEN** `.agents/skills/<skill-name>` already exists, the user has explicitly requested replacement, and `force=true`
- **THEN** the command SHALL direct the agent to rename the old entry to
  `<skill-name>.tmp-<suffix>`, create the replacement, and remove the backup
- **AND** SHALL direct the agent to report an intervening failure and restore the backup where possible

#### Scenario: Reject an unavailable skill name
- **WHEN** the positional skill name is absent from the active session's skill catalogue
- **THEN** the command SHALL report the unavailable name
- **AND** SHALL NOT export it

### Requirement: Claude Code compatibility link

When a `.claude` project directory exists, the command SHALL create
`.claude/skills` as necessary and create a relative symlink for an absent named
skill entry to its canonical `.agents/skills/<skill-name>` export. It SHALL NOT
create `.claude` solely to provide this link.

#### Scenario: Create an absent Claude link
- **WHEN** `.claude` exists and `.claude/skills/<skill-name>` is absent after a successful export
- **THEN** the command SHALL direct the agent to create the relative symlink

#### Scenario: Preserve a conflicting Claude entry
- **WHEN** `.claude/skills/<skill-name>` already exists and is not the canonical export symlink
- **THEN** the command SHALL leave it unchanged
- **AND** SHALL warn that Claude Code will use the existing entry until the user moves, deletes, or renames it

### Requirement: Package-shaped local output

The system SHALL provide a bound `export_skill` tool that returns the complete
rendered skill package using the existing MIME formatter. The entrypoint part
SHALL contain portable local frontmatter with `name`, `description`, and
`usage`; it SHALL omit Guide-only metadata and eligibility rules. Each package
member SHALL identify its package-relative location and permissions. The command
SHALL direct the agent to write the returned package locally without executing
scripts on the server's behalf.

#### Scenario: Export a skill entrypoint
- **WHEN** an agent exports a named skill
- **THEN** the command SHALL direct the agent to call `export_skill` and write its `SKILL.md` MIME part in the local package
- **AND** SHALL identify the canonical local package path in its completion report

#### Scenario: Preserve script safety
- **WHEN** a selected skill contains a script member
- **THEN** the export tool SHALL return that member with its permissions
- **AND** the command SHALL direct the agent to inspect and obtain authority before executing it locally
- **AND** SHALL NOT direct the server to execute it
