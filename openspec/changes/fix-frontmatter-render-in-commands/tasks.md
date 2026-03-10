## 1. Investigation
- [ ] 1.1 Find where command results construct `instruction` and `description` fields
- [ ] 1.2 Identify template context requirements (tool_prefix, INSTRUCTION_AGENT_INSTRUCTIONS, etc.)
- [ ] 1.3 Locate existing template rendering utilities in render package
- [ ] 1.4 Check if content rendering already handles this correctly

## 2. Implementation
- [ ] 2.1 Wire template renderer into command result construction
- [ ] 2.2 Ensure template context is available at render time
- [ ] 2.3 Handle missing context gracefully (fallback to unrendered)

## 3. Tests
- [ ] 3.1 Test instruction field rendering with tool_prefix
- [ ] 3.2 Test description field rendering
- [ ] 3.3 Test INSTRUCTION_AGENT_INSTRUCTIONS expansion
- [ ] 3.4 Test graceful handling of missing context

## 4. Documentation
- [ ] 4.1 Document template variables available in instruction/description fields
