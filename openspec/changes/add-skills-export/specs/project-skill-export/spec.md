## Purpose

Allow an agent to export explicitly selected, rendered Guide skill packages into
the current project using local skill-directory conventions without introducing
a server-side filesystem writer.

## ADDED Requirements

### Requirement: Project-scoped skill export command

The system SHALL provide a rendered `skills/export` command that directs the
agent to export Guide skills only into the active bound project's filesystem.
The command SHALL be addressable through the normal command surfaces, including
`guide://_skills/export/<destination>?skills=<comma-separated-skill-names>`.
It SHALL render its help and execution requirements from the active session's
available Guide skills and parsed command arguments.

#### Scenario: Export from a command URI
- **WHEN** an agent reads `guide://_skills/export/.agents?skills=workflow-review`
- **THEN** the command SHALL identify `.agents` as the project-relative destination
- **AND** SHALL identify `workflow-review` as the selected skill
- **AND** SHALL direct the agent to obtain and write the selected rendered skill package beneath that destination

#### Scenario: Export is limited to the current project
- **WHEN** an agent invokes the command while a project is bound
- **THEN** the command SHALL direct all export paths to be resolved beneath that project root
- **AND** SHALL NOT direct the agent to write a global, server-owned, or another project's skill directory

### Requirement: Destination selection

The command SHALL treat its optional positional destination as the project-relative
root for exported skill packages. When omitted, it SHALL default to `.agents`.
It SHALL present the default destination and, when known for the current agent,
that agent's project-local skills directory as alternatives.

#### Scenario: Use the default destination
- **WHEN** an agent invokes `skills/export` without a destination
- **THEN** the command SHALL identify `.agents` as the proposed destination

#### Scenario: Use an explicit destination
- **WHEN** an agent invokes `skills/export` with a relative destination
- **THEN** the command SHALL use that destination as the proposed package root

#### Scenario: Choose a destination interactively
- **WHEN** a destination is omitted and the client provides a native choice picker
- **THEN** the command SHALL direct the agent to offer the default and current-agent-specific project-local destination choices
- **AND** SHALL wait for the user's selection before exporting

### Requirement: Skill selection and confirmation

The command SHALL accept a comma-separated `skills` keyword containing the
public names of available Guide skills. When the keyword is omitted, it SHALL
offer the active session's available skills for selection. Before writing any
files, it SHALL require an explicit user confirmation of the destination and
selected skills.

#### Scenario: Select named skills
- **WHEN** an agent invokes `skills/export` with `skills=workflow-review,workflow-status`
- **THEN** the command SHALL identify exactly those two available skills for export

#### Scenario: Select skills interactively
- **WHEN** the `skills` keyword is omitted and the client provides a native multi-select picker
- **THEN** the command SHALL direct the agent to present every available Guide skill as a selectable option
- **AND** SHALL use the user's selections as the export set

#### Scenario: Use a non-interactive fallback
- **WHEN** a destination or skill selection is required but the client does not provide a native picker
- **THEN** the command SHALL direct the agent to present the same choices in a clear textual form
- **AND** SHALL wait for the user's answer before exporting

#### Scenario: Confirm an export
- **WHEN** the destination and selected skills are known
- **THEN** the command SHALL direct the agent to present a final confirmation before creating or overwriting any local files

#### Scenario: Reject an unavailable skill name
- **WHEN** the `skills` keyword includes a name absent from the active session's skill catalogue
- **THEN** the command SHALL report the unavailable name
- **AND** SHALL NOT export a partial selection

### Requirement: Package-shaped local output

The command SHALL direct the agent to export each selected skill as a portable
local skill package rooted at `SKILL.md`, preserving the rendered package
contents needed by that skill. It SHALL instruct the agent to inspect and
request individual optional resources, agents, or scripts as needed rather than
executing scripts on the server's behalf.

#### Scenario: Export a skill entrypoint
- **WHEN** the user confirms an export of a selected skill
- **THEN** the command SHALL direct the agent to write that skill's rendered entrypoint as `SKILL.md` in its local package
- **AND** SHALL identify the selected destination and local package path in its completion report

#### Scenario: Preserve script safety
- **WHEN** a selected skill references a script member
- **THEN** the command SHALL direct the agent to retrieve, inspect, and obtain authority before executing that script locally
- **AND** SHALL NOT direct the server to execute it
