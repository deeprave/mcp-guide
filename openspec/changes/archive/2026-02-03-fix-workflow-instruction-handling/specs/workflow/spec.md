## MODIFIED Requirements

### Requirement: Workflow Phase Transition Instructions
The system SHALL preserve and deliver frontmatter instructions from workflow phase change templates to ensure agents receive proper phase transition guidance including explicit consent confirmations and phase-specific restrictions.

#### Scenario: Phase transition with frontmatter instruction
- **WHEN** a workflow phase change occurs with a template containing frontmatter instruction
- **THEN** the Result object SHALL include both the rendered template content and the frontmatter instruction
- **AND** the instruction field SHALL contain the complete frontmatter instruction text
- **AND** no instruction content SHALL be lost or overwritten during processing

#### Scenario: Agent receives phase transition guidance
- **WHEN** an agent triggers a phase transition
- **THEN** the agent SHALL receive the frontmatter instruction containing explicit consent confirmation
- **AND** the agent SHALL receive phase-specific rules and restrictions
- **AND** the instruction SHALL be delivered alongside the rendered template content
