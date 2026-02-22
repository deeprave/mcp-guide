# session-management Specification Delta

## ADDED Requirements

### Requirement: Startup Instruction Template
The system SHALL render and queue a startup instruction template on project load/switch.

#### Scenario: Template location and frontmatter
- **WHEN** checking for startup instructions
- **THEN** look for `_startup.mustache` in project docroot
- **AND** template SHALL have `requires-startup-instruction: true` in frontmatter
- **AND** template SHALL have `type: agent/instruction` in frontmatter

#### Scenario: Template always rendered
- **WHEN** a project loads or switches
- **THEN** **always** attempt to render `_startup.mustache`
- **AND** template filtering via `requires-startup-instruction: true` is automatic
- **AND** no conditional logic needed before rendering

#### Scenario: Priority parameter for queue_instruction
- **WHEN** queueing an instruction
- **THEN** `queue_instruction()` SHALL accept optional `priority: bool = False` parameter
- **AND** when `priority=True`, insert instruction at front of queue (index 0)
- **AND** when `priority=False`, append to end of queue (existing behavior)

#### Scenario: Template rendering with flag set
- **WHEN** rendering `_startup.mustache`
- **AND** the `startup-instruction` flag is set and non-empty
- **THEN** template passes `requires-startup-instruction` check
- **AND** render with `{{feature_flags.startup-instruction}}` variable containing flag value
- **AND** if rendered content is non-blank, call `queue_instruction(content, priority=True)`
- **AND** instruction is **fire-and-forget** (queued for next dispatch, no agent acknowledgment expected)

#### Scenario: Template filtered when flag not set
- **WHEN** rendering `_startup.mustache`
- **AND** the `startup-instruction` flag is not set or empty
- **THEN** template is filtered by `requires-startup-instruction: true` directive
- **AND** rendering returns None
- **AND** no instruction is queued

#### Scenario: Blank content not queued
- **WHEN** `_startup.mustache` renders to blank content
- **THEN** do not queue any instruction
- **AND** continue normal project loading

#### Scenario: Project load trigger
- **WHEN** server starts with an existing project
- **OR** user switches to a different project
- **THEN** attempt to render `_startup.mustache`
- **AND** if content is non-blank, call `queue_instruction(content, priority=True)`
- **AND** instruction is inserted at front of queue
- **AND** instruction is queued for next dispatch opportunity

#### Scenario: Fire-and-forget instruction
- **WHEN** startup instruction is queued
- **THEN** instruction is sent via Result in next tool response
- **AND** no agent acknowledgment is expected
- **AND** agent processes instruction upon receipt

#### Scenario: No duplicate instructions
- **WHEN** a project is loaded multiple times
- **THEN** startup instruction SHALL only be queued once per load/switch event
- **AND** subsequent operations SHALL NOT re-queue the instruction
