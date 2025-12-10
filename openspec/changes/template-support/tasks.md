# Implementation Tasks

**Approval gate**: PENDING

## Phase 1: Template Rendering Engine

### 1. Template Detection and Rendering
- [ ] 1.1 Add chevron library integration (already dependency)
- [ ] 1.2 Implement .mustache file detection (check FileInfo.path.name.endswith('.mustache'))
- [ ] 1.3 Implement template rendering function with error handling
- [ ] 1.4 Add pass-through for non-template files
- [ ] 1.5 Handle template syntax errors with Result pattern
- [ ] 1.6 Add unit tests for template detection
- [ ] 1.7 Add unit tests for rendering success cases
- [ ] 1.8 Add unit tests for error handling

### 2. FileInfo Enhancement
- [ ] 2.1 Add optional ctime field to FileInfo model
- [ ] 2.2 Update file discovery to populate ctime when available
- [ ] 2.3 Implement size tracking for rendered templates
- [ ] 2.4 Update FileInfo creation in discover_category_files
- [ ] 2.5 Add unit tests for ctime handling
- [ ] 2.6 Add unit tests for size tracking

## Phase 2: Template Context Resolution

### 3. TemplateContext Infrastructure
- [ ] 3.1 Create TemplateContext class extending ChainMap[str, Any]
- [ ] 3.2 Implement type validation for keys (strings) and values (template-safe types)
- [ ] 3.3 Override new_child() to return TemplateContext instances
- [ ] 3.4 Override parents property to return TemplateContext | None
- [ ] 3.5 Add soft_delete() and hard_delete() methods with sentinel masking
- [ ] 3.6 Implement __getitem__ override to handle soft-deleted keys (KeyError)
- [ ] 3.7 Add unit tests for TemplateContext type validation
- [ ] 3.8 Add unit tests for scope chaining and priority resolution
- [ ] 3.9 Add unit tests for both deletion modes (hard/soft)

### 4. Context Builder with TemplateContext
- [ ] 4.1 Create template context builder using TemplateContext
- [ ] 4.2 Implement layered context creation (system → agent → project → collection → category → file)
- [ ] 4.3 Add datetime to ISO string conversion utilities
- [ ] 4.4 Add Path to string conversion utilities
- [ ] 4.5 Handle None values gracefully in context chain
- [ ] 4.6 Add unit tests for context builder with TemplateContext
- [ ] 4.7 Add unit tests for type conversions and None handling

### 5. Project Context Variables
- [ ] 5.1 Implement project context extraction from Project model
- [ ] 5.2 Add project.name, created_at, updated_at
- [ ] 5.3 Add project.categories list (category names)
- [ ] 5.4 Add project.collections list (collection names)
- [ ] 5.5 Add unit tests for project context
- [ ] 5.6 Test with missing project data

### 6. File Context Variables
- [ ] 6.1 Implement file context extraction from FileInfo
- [ ] 6.2 Add file.path, basename, category, collection
- [ ] 6.3 Add file.size (rendered size for templates)
- [ ] 6.4 Add file.mtime, ctime (optional)
- [ ] 6.5 Add unit tests for file context
- [ ] 6.6 Test with missing optional fields

### 7. Category Context Variables
- [ ] 7.1 Implement category context extraction from Category model
- [ ] 7.2 Add category.name, description
- [ ] 7.3 Add category.dir (relative path only, security requirement)
- [ ] 7.4 Ensure no docroot exposure
- [ ] 7.5 Add unit tests for category context
- [ ] 7.6 Test security constraints

### 8. Collection Context Variables
- [ ] 8.1 Implement collection context extraction from Collection model
- [ ] 8.2 Add collection.name, description
- [ ] 8.3 Add collection.categories list
- [ ] 8.4 Handle None when file not accessed via collection
- [ ] 8.5 Add unit tests for collection context
- [ ] 8.6 Test None handling

### 9. Agent Context Variables
- [ ] 9.1 Implement agent context extraction from session
- [ ] 9.2 Add @ variable (agent prompt character)
- [ ] 9.3 Add agent.name, version, prompt_prefix
- [ ] 9.4 Include all available agent info fields
- [ ] 9.5 Handle missing agent info gracefully
- [ ] 9.6 Add unit tests for agent context
- [ ] 9.7 Test with missing agent data

### 10. System Context Variables
- [ ] 10.1 Implement system context generation
- [ ] 10.2 Add now (ISO 8601 timestamp)
- [ ] 10.3 Add timestamp (Unix timestamp)
- [ ] 10.4 Ensure timestamp consistency within single render
- [ ] 10.5 Add unit tests for system context
- [ ] 10.6 Test timestamp consistency

## Phase 3: Integration and Error Handling

### 11. Template Error Handling
- [ ] 11.1 Implement Chevron error catching in template renderer
- [ ] 11.2 Add Result.failure responses for template errors
- [ ] 11.3 Add WARNING level logging for template errors
- [ ] 11.4 Create clear error messages with file paths
- [ ] 11.5 Add agent instructions for error resolution
- [ ] 11.6 Add unit tests for error scenarios
- [ ] 11.7 Test error logging
- [ ] 11.8 Test agent instruction content

### 12. Template Rendering Pipeline with TemplateContext
- [ ] 12.1 Integrate TemplateContext into template rendering pipeline
- [ ] 12.2 Build base context chain (system → agent → project → collection → category)
- [ ] 12.3 Create per-file contexts using TemplateContext.new_child() for isolation
- [ ] 12.4 Render templates with flattened TemplateContext (dict conversion)
- [ ] 12.5 Handle template rendering errors gracefully
- [ ] 12.6 Update FileInfo.size for rendered templates
- [ ] 12.7 Add integration tests for TemplateContext in rendering pipeline
- [ ] 12.8 Test context isolation between file renders

### 13. Content Tools Integration with TemplateContext
- [ ] 13.1 Integrate TemplateContext into get_category_content tool
- [ ] 13.2 Integrate TemplateContext into get_collection_content tool
- [ ] 13.3 Integrate TemplateContext into get_content tool
- [ ] 13.4 Ensure template rendering occurs after read, before format
- [ ] 13.5 Handle single file template responses
- [ ] 13.6 Handle MIME multipart with templates using TemplateContext
- [ ] 13.7 Add integration tests for TemplateContext in content tools
- [ ] 13.8 Test mixed template and non-template responses

## Phase 4: Testing and Documentation

### 14. Comprehensive Testing with TemplateContext
- [ ] 14.1 Add end-to-end template rendering tests with TemplateContext
- [ ] 14.2 Test all context variables in templates with scope chaining
- [ ] 14.3 Test TemplateContext priority resolution (file > category > collection > project > agent > system)
- [ ] 14.4 Test template error handling scenarios
- [ ] 14.5 Test integration with existing content tools
- [ ] 14.6 Performance testing (stateless TemplateContext approach)
- [ ] 14.7 Security testing (no docroot exposure, type validation)
- [ ] 14.8 Test TemplateContext with dockerized MCP scenarios
- [ ] 14.9 Test both hard and soft deletion modes
- [ ] 14.10 Test TemplateContext type validation edge cases

### 15. Documentation
- [ ] 15.1 Document TemplateContext class and usage patterns
- [ ] 15.2 Document template syntax and context variables
- [ ] 15.3 Document context variable reference with scope chaining
- [ ] 15.4 Document error types and solutions
- [ ] 15.5 Document security considerations (no docroot exposure)
- [ ] 15.6 Document integration with content tools
- [ ] 15.7 Add troubleshooting guide for templates and TemplateContext
- [ ] 15.8 Document agent instructions and template examples

## Summary

**Phase 1**: Template rendering engine and FileInfo enhancements (2 task groups)
**Phase 2**: TemplateContext and context resolution for all variable types (8 task groups)
**Phase 3**: Error handling and TemplateContext integration (3 task groups)
**Phase 4**: Testing and documentation with TemplateContext (2 task groups)

**Total**: 15 task groups, ~120 individual tasks

**Key Dependencies**:
- Chevron library (already added)
- Result pattern (existing)
- Content tools (existing)
- Session management (existing)
- TemplateContext (ChainMap-based, type-safe context system)

**Security Requirements**:
- No docroot path exposure
- Relative paths only
- Compatible with dockerized MCP
- Type validation for template contexts

**Performance Approach**:
- Stateless TemplateContext computation
- No caching (removed complexity)
- Fresh context chain on every render
- Efficient scope chaining with ChainMap
