## ADDED Requirements

### Requirement: Project-root instruction template
The system SHALL provide a mustache template at
`src/mcp_guide/templates/_system/_project-root.mustache` that instructs the agent
how to determine and send the correct project root when no project is currently bound.

The template SHALL:
- Instruct the agent to determine the project root using agent-side tool calls only
  (the server has no filesystem access)
- For git-controlled projects: instruct the agent to run
  `git rev-parse --git-common-dir` and derive the main repository root by stripping
  the trailing `/.git` component from the output, regardless of whether the agent is
  in a main worktree or a linked worktree
- For non-git-controlled projects or when git is unavailable: instruct the agent to
  use its current working directory as the project root
- Inform the agent that all relative paths used by the MCP server are relative to the
  project root it provides
- Instruct the agent to call `set_project` with the resolved absolute path

The template SHALL NOT reference `.guide.yaml` or any mcp-guide-specific file as a
marker for project root detection.

The template SHALL render correctly with no bound project — it MUST NOT reference
`project.*`, `workflow.*`, `client_working_dir`, or project-specific flag variables.

The template MAY use `agent.is_<name>` and `client.*` conditionals to tailor
instructions to the agent type or OS, but all conditional blocks MUST degrade
gracefully when agent/client info is not yet populated.

#### Scenario: Template renders with no bound project
- **WHEN** `render_content("_project-root", "_system")` is called with no project bound
- **THEN** the template renders without error
- **AND** the rendered output contains instructions for running `git rev-parse --git-common-dir`
- **AND** the rendered output contains a fallback instruction for non-git environments
- **AND** the rendered output instructs the agent to call `set_project`

#### Scenario: Template renders with bound project
- **WHEN** `render_content("_project-root", "_system")` is called with a project bound
- **THEN** the template renders identically to the unbound case
- **AND** no project-specific variables are referenced in the output

#### Scenario: Git worktree root resolution
- **WHEN** the agent is inside a linked git worktree (e.g. `.claude/worktrees/<name>`)
- **AND** the agent follows the template instructions
- **THEN** the agent runs `git rev-parse --git-common-dir`
- **AND** derives the main repository root by stripping the trailing `/.git` component
- **AND** sends that path to `set_project`, not the worktree subdirectory

#### Scenario: Non-git project root resolution
- **WHEN** `git rev-parse` fails or git is not available
- **AND** the agent follows the template instructions
- **THEN** the agent uses its current working directory as the project root
- **AND** sends that path to `set_project`

---

### Requirement: Path-relativity contract communicated to agent
The system SHALL include in the project-root instruction template an explicit statement
that all relative paths used by the MCP server are relative to the project root
provided by the agent via `set_project`.

#### Scenario: Agent informed of path relativity
- **WHEN** the `_project-root` template is rendered and returned to the agent
- **THEN** the output explicitly states that relative paths in MCP responses are
  relative to the project root
- **AND** this statement appears unconditionally, not inside any agent-type guard
