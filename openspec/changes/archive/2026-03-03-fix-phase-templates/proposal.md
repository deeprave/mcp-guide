# Change: Fix Phase and Feature Conditional Logic in Templates

## Why

Templates throughout the system contain hardcoded references to workflow phases (like "check") and features (like "openspec") without checking if they're enabled in the current project configuration. This causes:

1. **Invalid phase references**: Templates mention phases that don't exist in the current workflow (e.g., mentioning "check" phase in a 3-phase `[discussion, implementation, review]` workflow)
2. **Feature leakage**: Templates reference openspec-specific content without checking if openspec is enabled
3. **Inconsistent consent language**: Some templates mention "explicit consent" without also mentioning "explicit request", causing agents to not recognize user requests as valid consent

## What Changes

- Audit **all templates** in the system (workflow, commands, checks, guide, review, openspec, etc.)
- Wrap phase-specific content in `{{#workflow.phases.{phase}}}...{{/workflow.phases.{phase}}}` conditionals
- Wrap openspec-specific content in `{{#openspec}}...{{/openspec}}` conditionals
- Update consent language to consistently use "explicit consent or request" instead of just "explicit consent"
- Use `{{workflow.phases.{phase}.next}}` or `{{workflow.next}}` instead of hardcoding next phase names
- Ensure `{{#workflow.consent.entry}}` and `{{#workflow.consent.exit}}` are used appropriately

**Note**: `discussion` and `implementation` phases are mandatory when workflow is enabled and can be assumed always available.

## Impact

- **Affected specs**: `workflow-templates`, `template-rendering`, potentially `help-template-system`
- **Affected code**: All template files in `src/mcp_guide/templates/`
- **Breaking changes**: None - this fixes existing bugs
- **Benefits**:
  - Templates correctly adapt to project configuration
  - 3-phase workflows work without mentioning non-existent phases
  - OpenSpec-disabled projects don't see openspec references
  - Agents recognize both "consent" and "request" as valid explicit permission
