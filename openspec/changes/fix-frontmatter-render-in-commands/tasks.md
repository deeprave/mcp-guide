## 1. Investigation
- [ ] 1.1 Find where command results construct `instruction` and `description` fields
- [ ] 1.2 Identify template context requirements (tool_prefix, INSTRUCTION_AGENT_INSTRUCTIONS, etc.)
- [ ] 1.3 Locate existing template rendering utilities in render package
- [ ] 1.4 Check if content rendering already handles this correctly
- [ ] 1.5 Investigate how partial frontmatter is currently merged (regardless of usage)

## 2. Implementation
- [ ] 2.1 Wire template renderer into command result construction
- [ ] 2.2 Ensure template context is available at render time
- [ ] 2.3 Handle missing context gracefully (fallback to unrendered)
- [ ] 2.4 Track which partials are actually rendered during Mustache processing
- [ ] 2.5 Only merge frontmatter from partials that are actually used in output

## 3. Tests
- [ ] 3.1 Test instruction field rendering with tool_prefix
- [ ] 3.2 Test description field rendering
- [ ] 3.3 Test INSTRUCTION_AGENT_INSTRUCTIONS expansion
- [ ] 3.4 Test graceful handling of missing context
- [ ] 3.5 Test partial instruction NOT applied when partial isn't rendered
- [ ] 3.6 Test partial instruction IS applied when partial is rendered
- [ ] 3.7 Test status command displays correctly (not overridden by unused _client-info)

## 4. Documentation
- [ ] 4.1 Document template variables available in instruction/description fields
