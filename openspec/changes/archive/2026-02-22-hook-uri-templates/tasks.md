# Tasks: Hook URI Templates

## Implementation Tasks

### 1. Template Content Infrastructure
- [ ] Create `_hooks/` category for hook template content
- [ ] Create template files for different workflow modes:
  - [ ] `_hooks/guided.md` - Guided mode instructions
  - [ ] `_hooks/normal.md` - Normal mode instructions
  - [ ] `_hooks/review.md` - Review mode instructions
- [ ] Add feature flag support to hook templates
- [ ] Add template variable support (`{{@}}`, `{{_workflow.mode}}`, etc.)

### 2. URI Template Resolution
- [ ] Extend guide:// URI scheme to support template variables
- [ ] Add template variable resolution before URI processing
- [ ] Support dynamic category/collection resolution
- [ ] Handle template variable errors gracefully

### 3. Agent Integration
- [ ] Update hook scripts to output URI instructions instead of static text
- [ ] Add frontmatter metadata for agent instruction type
- [ ] Ensure agents recognize and follow guide:// URIs with templates
- [ ] Test agent workflow: script → URI → template resolution → content

### 4. Testing and Validation
- [ ] Unit tests for template variable resolution in URIs
- [ ] Integration tests for hook script → agent workflow
- [ ] Test feature flag integration in hook templates
- [ ] Test error handling for invalid template variables
- [ ] Validate backward compatibility with existing static scripts

### 5. Documentation
- [ ] Document hook URI template syntax
- [ ] Provide examples of template-enabled hook content
- [ ] Update agent configuration documentation
- [ ] Add troubleshooting guide for template resolution issues

## Dependencies

### Required Before Implementation
- **add-guide-uri-scheme**: Must be complete for URI resolution
- **template-support**: Must be complete for template variable rendering
- **add-feature-flags**: Must be complete for feature flag support in templates

### Validation Criteria
- Hook scripts output valid URI instructions with template syntax
- Agents successfully resolve template variables in guide:// URIs
- Template content renders with feature flags and context variables
- No regression in existing static hook functionality
