# Implementation Tasks

## 1. Feature Flag Definition
- [x] 1.1 Add `startup-instruction` to feature flag schema (string type, optional)
- [ ] 1.2 Document flag in feature flags documentation

## 2. Expression Validation
- [x] 2.1 Create expression parser to extract categories/collections
- [x] 2.2 Implement validation logic:
  - [x] Parse expression into components
  - [x] Validate each category exists in project
  - [x] Validate each collection exists in project
  - [x] Ignore patterns (validated at runtime by get_content)
- [x] 2.3 Add validation to flag setter (reject invalid expressions)
- [x] 2.4 Return clear error messages for invalid expressions

## 3. Startup Template
- [x] 3.1 Create `_startup.md` template in templates directory
- [x] 3.2 Add frontmatter: `requires-startup-instruction: true`
- [x] 3.3 Add frontmatter: `type: agent/instruction`
- [x] 3.4 Template content with `{{feature_flags.startup-instruction}}` variable
- [x] 3.5 Include instruction to call `get_content("{{feature_flags.startup-instruction}}")`
- [x] 3.6 Include confirmation requirement

## 4. Template Rendering Support
- [x] 4.1 Add `requires-startup-instruction` to requires-* directive handling (already generic)
- [x] 4.2 Ensure template filtered when flag not set or empty
- [x] 4.3 Pass `startup_instruction` flag value to template context
- [x] 4.4 Handle blank rendered content (don't queue)

## 5. Project Load Detection
- [x] 5.1 Add project load callback mechanism to Session
- [x] 5.2 Add project switch event detection (via set_project)
- [x] 5.3 Ensure events trigger on:
  - [x] Server startup with existing project
  - [x] User switches to different project via set_project

## 6. Template Rendering and Queueing
- [x] 6.1 Add optional `priority: bool = False` parameter to `queue_instruction()` method
- [x] 6.2 When `priority=True`, insert instruction at front of queue (index 0)
- [x] 6.3 When `priority=False`, append to end of queue (existing behavior)
- [x] 6.4 On project load/switch, **always** render `_startup`
- [x] 6.5 Template automatically filtered if flag not set (via `requires-startup-instruction`)
- [x] 6.6 If rendered (not filtered) and content is non-blank, call `queue_instruction(content, priority=True)`
- [x] 6.7 Ensure instruction only queued once per project load/switch

## 7. Testing
- [x] 7.1 Test with flag not set (template filtered, no instruction)
- [x] 7.2 Test with empty flag (template filtered, no instruction)
- [x] 7.3 Test with valid collection expression
- [x] 7.4 Test with valid category expression
- [x] 7.5 Test with valid category+pattern expression
- [x] 7.6 Test with multiple expressions
- [x] 7.7 Test validation rejects invalid categories
- [x] 7.8 Test validation rejects invalid collections
- [x] 7.9 Test template renders with flag value
- [x] 7.10 Test instruction triggers on project load
- [x] 7.11 Test instruction triggers on project switch
- [x] 7.12 Test instruction not duplicated on multiple switches
- [x] 7.13 Test blank template content not queued

## 8. Documentation
- [ ] 8.1 Document `startup-instruction` flag in feature flags guide
- [ ] 8.2 Add examples of valid expressions
- [ ] 8.3 Document `_startup` template
- [ ] 8.4 Document validation behavior
- [ ] 8.5 Add troubleshooting section for common errors
- [ ] 8.6 Update all feature flag documentation to include `startup-instruction`
- [ ] 8.7 Document fire-and-forget behavior (queued, sent via Result, no acknowledgment)
- [ ] 8.8 Document highest-priority queueing behavior
