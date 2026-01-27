# template-system Specification Delta

## ADDED Requirements

### Requirement: Unified Template Renderer
The system SHALL provide a unified template rendering interface for all template types.

#### Scenario: Render any template type
- WHEN a template is rendered
- THEN the system SHALL use unified renderer regardless of template type
- AND frontmatter rules SHALL be parsed consistently
- AND template type routing SHALL be handled automatically

#### Scenario: Frontmatter parsing consistency
- WHEN template frontmatter is parsed
- THEN all templates SHALL use same parsing logic
- AND frontmatter rules SHALL be applied uniformly
- AND no special cases exist for different template locations

### Requirement: System Template Type Handling
The system SHALL handle special template types with consistent routing.

#### Scenario: Command template rendering
- WHEN a command template is rendered
- THEN system SHALL route to command template handler
- AND apply command-specific context
- AND follow command frontmatter rules

#### Scenario: Workflow template rendering
- WHEN a workflow template is rendered
- THEN system SHALL route to workflow template handler
- AND apply workflow-specific context
- AND follow workflow frontmatter rules

#### Scenario: OpenSpec template rendering
- WHEN an openspec template is rendered
- THEN system SHALL route to openspec template handler
- AND apply openspec-specific context
- AND follow openspec frontmatter rules

#### Scenario: Common template rendering
- WHEN a common template is rendered
- THEN system SHALL route to common template handler
- AND apply common template context
- AND follow common frontmatter rules

## MODIFIED Requirements

### Requirement: Template Discovery
Template discovery SHALL work with unified rendering system.

#### Scenario: Discover templates by type
- WHEN templates are discovered
- THEN system SHALL identify template type from location or frontmatter
- AND route to appropriate handler in unified system
- AND maintain backward compatibility with existing templates
