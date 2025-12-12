# Implementation Tasks

**Approval gate**: PENDING

## Phase 0: Template Lambda Functions (COMPLETED ✅)

### 0. Template Lambda Functions Infrastructure
- [x] 0.1 Create TemplateFunctions class with ChainMap context integration
- [x] 0.2 Create SyntaxHighlighter class with optional Pygments integration
- [x] 0.3 Implement format_date lambda function for datetime formatting
- [x] 0.4 Implement truncate lambda function for text truncation with ellipses
- [x] 0.5 Implement highlight_code lambda function for syntax highlighting
- [x] 0.6 Support Mustache lambda specification (text, render parameters)
- [x] 0.7 Add comprehensive unit tests for all lambda functions
- [x] 0.8 Add Chevron integration test for full template rendering pipeline
- [x] 0.9 Implement graceful fallback for missing Pygments dependency

**Files Created:**
- `guide/template_functions.py` - Core lambda functions implementation
- `tests/test_template_functions.py` - Comprehensive test suite

**Lambda Functions Available:**
- `format_date`: Date formatting with strftime patterns (e.g., `{{#format_date}}%Y-%m-%d{{created_at}}{{/format_date}}`)
- `truncate`: Text truncation with ellipses (e.g., `{{#truncate}}50{{description}}{{/truncate}}`)
- `highlight_code`: Syntax highlighting with markdown code blocks (e.g., `{{#highlight_code}}python{{code_snippet}}{{/highlight_code}}`)

## Phase 1: Template Rendering Engine (COMPLETED ✅)

### 1. Template Detection and Rendering
- [x] 1.1 Add chevron library integration (already dependency)
- [x] 1.2 Implement .mustache file detection (check FileInfo.path.name.endswith('.mustache'))
- [x] 1.3 Implement template rendering function with error handling
- [x] 1.4 Add pass-through for non-template files
- [x] 1.5 Handle template syntax errors with Result pattern
- [x] 1.6 Add unit tests for template detection
- [x] 1.7 Add unit tests for rendering success cases
- [x] 1.8 Add unit tests for error handling

### 2. FileInfo Enhancement
- [x] 2.1 Add optional ctime field to FileInfo model
- [x] 2.2 Update file discovery to populate ctime when available
- [x] 2.3 Implement size tracking for rendered templates
- [x] 2.4 Update FileInfo creation in discover_category_files
- [x] 2.5 Add unit tests for ctime handling
- [x] 2.6 Add unit tests for size tracking

**Files Created/Modified:**
- `src/mcp_guide/utils/template_renderer.py` - Core template rendering functionality
- `tests/test_template_renderer.py` - Comprehensive test suite (11 test cases, 100% coverage)
- `src/mcp_guide/utils/file_discovery.py` - Added ctime field to FileInfo model

**Key Features Implemented:**
- Template detection using `.mustache` extension
- Chevron integration with lambda function support
- Result pattern for error handling
- Pass-through for non-template files
- Size tracking for rendered templates
- Optional ctime field with graceful fallback

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

### 12. Template Rendering Pipeline with TemplateContext and Lambda Functions
- [ ] 12.1 Integrate TemplateContext into template rendering pipeline
- [ ] 12.2 Build base context chain (system → agent → project → collection → category)
- [ ] 12.3 Create per-file contexts using TemplateContext.new_child() for isolation
- [ ] 12.4 Inject TemplateFunctions lambda functions into context
- [ ] 12.5 Render templates with flattened TemplateContext (dict conversion)
- [ ] 12.6 Handle template rendering errors gracefully
- [ ] 12.7 Update FileInfo.size for rendered templates
- [ ] 12.8 Add integration tests for TemplateContext in rendering pipeline
- [ ] 12.9 Test context isolation between file renders
- [ ] 12.10 Test lambda function integration with context variables

### 13. Content Tools Integration with TemplateContext and Lambda Functions
- [ ] 13.1 Integrate TemplateContext into get_category_content tool
- [ ] 13.2 Integrate TemplateContext into get_collection_content tool
- [ ] 13.3 Integrate TemplateContext into get_content tool
- [ ] 13.4 Ensure template rendering occurs after read, before format
- [ ] 13.5 Handle single file template responses
- [ ] 13.6 Handle MIME multipart with templates using TemplateContext
- [ ] 13.7 Add integration tests for TemplateContext in content tools
- [ ] 13.8 Test mixed template and non-template responses
- [ ] 13.9 Test lambda functions in content tool responses

## Phase 4: Testing and Documentation

### 14. Comprehensive Testing with TemplateContext and Lambda Functions
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
- [ ] 14.11 Test lambda functions with various data sources (files, loops, timestamps)
- [ ] 14.12 Test syntax highlighting with and without Pygments

### 15. Documentation
- [ ] 15.1 Document TemplateContext class and usage patterns
- [ ] 15.2 Document template syntax and context variables
- [ ] 15.3 Document context variable reference with scope chaining
- [ ] 15.4 Document lambda functions (format_date, truncate, highlight_code)
- [ ] 15.5 Document error types and solutions
- [ ] 15.6 Document security considerations (no docroot exposure)
- [ ] 15.7 Document integration with content tools
- [ ] 15.8 Add troubleshooting guide for templates and TemplateContext
- [ ] 15.9 Document agent instructions and template examples
- [ ] 15.10 Document lambda function usage patterns and examples

## Summary

**Phase 0**: Template lambda functions infrastructure (COMPLETED ✅)
**Phase 1**: Template rendering engine and FileInfo enhancements (2 task groups)
**Phase 2**: TemplateContext and context resolution for all variable types (8 task groups)
**Phase 3**: Error handling and TemplateContext integration with lambda functions (3 task groups)
**Phase 4**: Testing and documentation with TemplateContext and lambda functions (2 task groups)

**Total**: 16 task groups, ~130 individual tasks (9 completed in Phase 0)

**Key Dependencies**:
- Chevron library (already added)
- Result pattern (existing)
- Content tools (existing)
- Session management (existing)
- TemplateContext (ChainMap-based, type-safe context system)
- TemplateFunctions (lambda functions for advanced template features)

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
- Class-based lambda functions for clean dependency management
