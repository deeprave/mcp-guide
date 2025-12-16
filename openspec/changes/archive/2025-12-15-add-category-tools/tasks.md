# Implementation Tasks

## 0. Tool Registration Refactor (PREREQUISITE) - COMPLETE ✅
- [x] 0.1 Update tool-infrastructure spec with decorator pattern (deferred to 0.9)
- [x] 0.2 Add ADR-008 revision documenting decorator approach (deferred to 0.9)
- [x] 0.3 Implement ContextVar test mode control in tool_decorator.py
- [x] 0.4 Update ExtMcpToolDecorator with args_class parameter
- [x] 0.5 Create _ToolsProxy in server.py
- [x] 0.6 Simplify ToolArguments (remove lazy registration)
- [x] 0.7 Update tool_example.py to new pattern
- [x] 0.8 Update tool_category.py to new pattern (was 0.6 in plan)
- [x] 0.9 Update specifications (tool-infrastructure, ADR-008)
- [x] 0.10 Final verification and integration tests

## 1. Validation Functions ✅ COMPLETE
- [x] 1.1 Implement category name validation (use existing)
- [x] 1.2 Implement directory path validation
- [x] 1.3 Implement description validation
- [x] 1.4 Implement pattern validation
- [x] 1.5 Add traversal prevention checks

## 2. category_list Tool ✅ COMPLETE
- [x] 2.1 Implement argument schema
- [x] 2.2 Get all categories from configuration
- [x] 2.3 Format response with name, dir, description, patterns
- [x] 2.4 Return Result response

## 3. category_add Tool ✅ COMPLETE
- [x] 3.1 Implement argument schema
- [x] 3.2 Validate all inputs
- [x] 3.3 Check category doesn't exist
- [x] 3.4 Create category in configuration
- [x] 3.5 Persist configuration
- [x] 3.6 Return Result response

## 4. category_remove Tool ✅ COMPLETE
- [x] 4.1 Implement argument schema
- [x] 4.2 Validate category exists
- [x] 4.3 Remove from all collections
- [x] 4.4 Remove from configuration
- [x] 4.5 Persist configuration
- [x] 4.6 Return Result response

## 5. category_change Tool ✅ COMPLETE
- [x] 5.1 Implement argument schema
- [x] 5.2 Validate category exists
- [x] 5.3 Validate new name if renaming
- [x] 5.4 Validate all new values
- [x] 5.5 Replace category configuration
- [x] 5.6 Update collections if renamed
- [x] 5.7 Persist configuration
- [x] 5.8 Return Result response

## 6. category_update Tool ✅ COMPLETE
- [x] 6.1 Implement argument schema
- [x] 6.2 Validate category exists
- [x] 6.3 Add patterns if specified
- [x] 6.4 Remove patterns if specified
- [x] 6.5 Persist configuration
- [x] 6.6 Return Result response

## 7. Configuration Persistence ✅ COMPLETE
- [x] 7.1 Implement safe configuration write
- [x] 7.2 Add file locking for concurrent access
- [x] 7.3 Validate configuration before write
- [x] 7.4 Handle write errors gracefully

## 8. Testing ✅ COMPLETE
- [x] 8.1 Unit tests for validation functions
- [x] 8.2 Unit tests for each tool
- [x] 8.3 Integration tests for configuration persistence
- [x] 8.4 Test auto-removal from collections
- [x] 8.5 Test error cases and validation
