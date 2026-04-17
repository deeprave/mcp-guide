## MODIFIED Requirements

### Requirement: Template Context Preserves Display-Safe Flag Values

Templates SHALL be able to display configured flag values using stable,
user-facing representations without changing the generic list-wrapping
semantics used elsewhere in the rendering system.

#### Scenario: Custom workflow list renders as plain phase names for display
- **GIVEN** the configured workflow flag value is `[discussion, implementation, check, review]`
- **AND** the rendering system continues to use generic indexed list wrappers for list iteration
- **WHEN** a project or workflow-aware template displays the configured flag value for the user
- **THEN** the rendered output uses plain phase names
- **AND** it does NOT render the internal wrapper-object representation containing `value`, `first`, and `last`

#### Scenario: Dict-like flag renders as stable display text
- **GIVEN** a configured flag value is a dict or contains nested dict/list values
- **WHEN** a template displays that flag value through a display-oriented flag projection
- **THEN** the rendered output is a stable user-facing string representation
- **AND** it does NOT expose internal wrapper-object representations from generic list conversion

#### Scenario: Generic list rendering semantics remain unchanged
- **GIVEN** a non-workflow list in template context
- **WHEN** template rendering prepares that list for iteration
- **THEN** the system continues to expose the generic indexed wrapper behavior used by existing templates
- **AND** this workflow-render fix does not change global list conversion behavior
