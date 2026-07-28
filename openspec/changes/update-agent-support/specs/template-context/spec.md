## ADDED Requirements

### Requirement: Prompt-aware template guidance
The template context SHALL suppress prompt-invocation guidance for agents whose prompt prefix is absent.

#### Scenario: Render for an agent without prompt support
- **WHEN** a template is rendered for an agent with `prompt_prefix=None`
- **THEN** the rendered content SHALL omit prompt invocation syntax
