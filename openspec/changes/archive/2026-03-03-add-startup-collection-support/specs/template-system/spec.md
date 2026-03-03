# template-system Specification Delta

## ADDED Requirements

### Requirement: Startup Instruction Template Support
The system SHALL support rendering startup instruction templates with flag-based filtering.

#### Scenario: requires-startup-instruction directive
- **WHEN** a template has `requires-startup-instruction: true` in frontmatter
- **AND** the `startup-instruction` flag is not set or empty
- **THEN** the template SHALL be filtered out (not rendered)

#### Scenario: Template context with flag value
- **WHEN** rendering a template with `requires-startup-instruction: true`
- **AND** the `startup-instruction` flag is set and non-empty
- **THEN** include `{{feature_flags.startup-instruction}}` variable in template context
- **AND** the variable SHALL contain the flag value

#### Scenario: Startup template location
- **WHEN** looking for startup instruction template
- **THEN** check for `_startup.mustache` in project docroot
- **AND** template SHALL be treated like other instruction templates

#### Scenario: Template example structure
- **WHEN** creating a startup instruction template
- **THEN** frontmatter SHALL include:
  ```yaml
  type: agent/instruction
  requires-startup-instruction: true
  instruction: >
    Follow these startup instructions.
  ```
- **AND** content SHALL reference `{{feature_flags.startup-instruction}}` for the expression
- **AND** content SHALL instruct agent to call `get_content("{{feature_flags.startup-instruction}}")`
