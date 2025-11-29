# Implementation Tasks

## 0. Tool Registration Refactor (PREREQUISITE) - NEARLY COMPLETE
- [x] 0.1 Update tool-infrastructure spec with decorator pattern (deferred to 0.9)
- [x] 0.2 Add ADR-008 revision documenting decorator approach (deferred to 0.9)
- [x] 0.3 Implement ContextVar test mode control in tool_decorator.py
- [x] 0.4 Update ExtMcpToolDecorator with args_class parameter
- [x] 0.5 Create _ToolsProxy in server.py
- [x] 0.6 Simplify ToolArguments (remove lazy registration)
- [x] 0.7 Update tool_example.py to new pattern
- [x] 0.8 Update tool_category.py to new pattern (was 0.6 in plan)
- [ ] 0.9 Update specifications (tool-infrastructure, ADR-008)
- [ ] 0.10 Final verification and integration tests

## 1. Validation Functions ✅ COMPLETE
- [x] 1.1 Implement category name validation (use existing)
- [x] 1.2 Implement directory path validation
- [x] 1.3 Implement description validation
- [x] 1.4 Implement pattern validation
- [x] 1.5 Add traversal prevention checks

## 2. category_list Tool ⚠️ NEEDS REWORK (registration pattern)
- [ ] 2.1 Implement argument schema (needs decorator update)
- [x] 2.2 Get all categories from configuration
- [x] 2.3 Format response with name, dir, description, patterns
- [x] 2.4 Return Result response

## 3. category_add Tool
- [ ] 3.1 Implement argument schema
- [ ] 3.2 Validate all inputs
- [ ] 3.3 Check category doesn't exist
- [ ] 3.4 Create category in configuration
- [ ] 3.5 Persist configuration
- [ ] 3.6 Return Result response

## 4. category_remove Tool
- [ ] 4.1 Implement argument schema
- [ ] 4.2 Validate category exists
- [ ] 4.3 Remove from all collections
- [ ] 4.4 Remove from configuration
- [ ] 4.5 Persist configuration
- [ ] 4.6 Return Result response

## 5. category_change Tool
- [ ] 5.1 Implement argument schema
- [ ] 5.2 Validate category exists
- [ ] 5.3 Validate new name if renaming
- [ ] 5.4 Validate all new values
- [ ] 5.5 Replace category configuration
- [ ] 5.6 Update collections if renamed
- [ ] 5.7 Persist configuration
- [ ] 5.8 Return Result response

## 6. category_update Tool
- [ ] 6.1 Implement argument schema
- [ ] 6.2 Validate category exists
- [ ] 6.3 Add patterns if specified
- [ ] 6.4 Remove patterns if specified
- [ ] 6.5 Persist configuration
- [ ] 6.6 Return Result response

## 7. Configuration Persistence
- [ ] 7.1 Implement safe configuration write
- [ ] 7.2 Add file locking for concurrent access
- [ ] 7.3 Validate configuration before write
- [ ] 7.4 Handle write errors gracefully

## 8. Testing
- [ ] 8.1 Unit tests for validation functions
- [ ] 8.2 Unit tests for each tool
- [ ] 8.3 Integration tests for configuration persistence
- [ ] 8.4 Test auto-removal from collections
- [ ] 8.5 Test error cases and validation

## 9. Documentation
- [ ] 9.1 Document tool usage and examples
- [ ] 9.2 Document validation rules
- [ ] 9.3 Document side effects (auto-removal)
- [ ] 9.4 Add troubleshooting guide
