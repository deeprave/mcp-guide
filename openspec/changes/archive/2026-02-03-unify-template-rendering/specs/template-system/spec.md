# template-system Specification Delta

## ADDED Requirements

### Requirement: Type-Safe Frontmatter
The system SHALL provide a `Frontmatter` class extending `dict` with type-safe accessors.

#### Scenario: Type-safe string access
- WHEN accessing string values via `get_str()`
- THEN values SHALL be converted to lowercase
- AND None SHALL be returned if key is missing
- AND TypeError SHALL be raised if value is not a string

#### Scenario: Type-safe list access
- WHEN accessing list values via `get_list()`
- THEN single values SHALL be wrapped in a list
- AND tuples SHALL be converted to lists
- AND None SHALL be returned if key is missing

#### Scenario: Type-safe dict access
- WHEN accessing dict values via `get_dict()`
- THEN dict values SHALL be returned as-is
- AND None SHALL be returned if key is missing
- AND TypeError SHALL be raised if value is not a dict

#### Scenario: Type-safe bool access
- WHEN accessing bool values via `get_bool()`
- THEN bool values SHALL be returned as-is
- AND None SHALL be returned if key is missing
- AND TypeError SHALL be raised if value is not a bool

### Requirement: Frontmatter Key Constants
The system SHALL define constants for frontmatter keys.

#### Scenario: Use constants for frontmatter keys
- WHEN accessing frontmatter keys
- THEN system SHALL use defined constants
- AND constants SHALL be: FM_INSTRUCTION, FM_TYPE, FM_DESCRIPTION, FM_REQUIRES_PREFIX, FM_CATEGORY, FM_USAGE, FM_ALIASES, FM_INCLUDES

### Requirement: Template Rendering Function
The system SHALL provide a `render_template()` function for rendering templates with consistent frontmatter handling.

#### Scenario: Render template with frontmatter
- WHEN a template is rendered via `render_template()`
- THEN frontmatter SHALL be parsed consistently
- AND `requires-*` directives SHALL be evaluated against project flags
- AND templates with unmet requirements SHALL return None
- AND frontmatter variables SHALL be added to rendering context

#### Scenario: Template vs non-template files
- WHEN a file without template extension is rendered
- THEN frontmatter SHALL be parsed
- AND `requires-*` directives SHALL be evaluated
- AND content SHALL be returned as-is without Chevron rendering
- WHEN a file with template extension is rendered
- THEN content SHALL be rendered with Chevron after frontmatter processing

#### Scenario: Context layering
- WHEN a template is rendered
- THEN base context SHALL be retrieved from cache
- AND context SHALL be layered: base → frontmatter vars → caller context
- AND frontmatter vars SHALL exclude `requires-*` and `includes` keys
- AND final context SHALL be used for rendering

#### Scenario: Error handling
- WHEN rendering fails
- THEN error SHALL be logged
- AND function SHALL return None
- AND caller SHALL not receive error details

### Requirement: RenderedContent Type
The system SHALL provide a `RenderedContent` dataclass extending `Content`.

#### Scenario: Return rendered content
- WHEN a template is successfully rendered
- THEN system SHALL return `RenderedContent` with:
  - Inherited: frontmatter (Frontmatter), frontmatter_length, content, content_length
  - Added: template_path, template_name

#### Scenario: Instruction property
- WHEN accessing `RenderedContent.instruction`
- THEN property SHALL return instruction from frontmatter if present
- OR return default instruction for template type if not present

#### Scenario: Template type property
- WHEN accessing `RenderedContent.template_type`
- THEN property SHALL return type from frontmatter if present
- OR return default type (AGENT_INSTRUCTION) if not present
