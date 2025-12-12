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
- [x] 1.9 Enhanced error handling with logging and exception types
- [x] 1.10 Added proper Result.instruction consistency for agent guidance

### 2. FileInfo Enhancement
- [x] 2.1 Add optional ctime field to FileInfo model
- [x] 2.2 Update file discovery to populate ctime when available (simplified, removed hasattr check)
- [x] 2.3 Implement size tracking for rendered templates
- [x] 2.4 Update FileInfo creation in discover_category_files
- [x] 2.5 Add unit tests for ctime handling
- [x] 2.6 Add unit tests for size tracking
- [x] 2.7 Updated ctime documentation to clarify platform-dependent behavior (Unix: inode change time, Windows: creation time)

### 3. Code Quality and Security Enhancements (COMPLETED ✅)
- [x] 3.1 Centralized template parsing with _parse_template_args() helper
- [x] 3.2 Enhanced variable name validation to support dotted paths (e.g., project.name)
- [x] 3.3 Comprehensive security test coverage for all lambda functions
- [x] 3.4 Enhanced _safe_lambda with exception type logging and better error context
- [x] 3.5 Full MyPy strict type compliance
- [x] 3.6 Ruff linting and formatting compliance
- [x] 3.7 20 comprehensive test cases with 98%+ coverage

**Files Created/Modified:**
- `src/mcp_guide/utils/template_renderer.py` - Core template rendering functionality with enhanced error handling
- `tests/test_template_renderer.py` - Comprehensive test suite (11 test cases, 100% coverage)
- `src/mcp_guide/utils/file_discovery.py` - Added ctime field to FileInfo model with platform-dependent documentation
- `src/mcp_guide/utils/template_functions.py` - Moved from guide/ to proper src structure, enhanced with centralized parsing
- `tests/test_template_functions.py` - Expanded to 20 comprehensive test cases with 98% coverage

**Key Features Implemented:**
- Template detection using `.mustache` extension
- Chevron integration with lambda function support
- Result pattern for error handling with proper instruction consistency
- Pass-through for non-template files
- Size tracking for rendered templates
- Optional ctime field with platform-dependent documentation
- Enhanced error diagnostics with exception types and logging
- Centralized template parsing supporting dotted paths (e.g., `{{project.name}}`)
- Comprehensive security validation and test coverage
- Full MyPy strict type compliance and code quality standards

## Phase 2: Template Context Resolution (READY FOR IMPLEMENTATION)

**See design.md for architecture decisions and technical details.**

### 3. TemplateContext Infrastructure (TDD: Red-Green-Refactor)
- [ ] 3.1 **RED**: Create failing test for TemplateContext class extending ChainMap[str, Any]
- [ ] 3.2 **GREEN**: Implement basic TemplateContext class with ChainMap inheritance
- [ ] 3.3 **RED**: Create failing test for type validation (keys=strings, values=template-safe)
- [ ] 3.4 **GREEN**: Implement type validation in __setitem__ and __init__
- [ ] 3.5 **RED**: Create failing test for new_child() returning TemplateContext instances
- [ ] 3.6 **GREEN**: Override new_child() method with proper return type
- [ ] 3.7 **RED**: Create failing test for parents property returning TemplateContext | None
- [ ] 3.8 **GREEN**: Override parents property with correct typing
- [ ] 3.9 **RED**: Create failing tests for soft_delete() and hard_delete() methods
- [ ] 3.10 **GREEN**: Implement deletion methods with sentinel masking
- [ ] 3.11 **RED**: Create failing test for __getitem__ handling soft-deleted keys (KeyError)
- [ ] 3.12 **GREEN**: Override __getitem__ to handle soft deletion
- [ ] 3.13 **REFACTOR**: Clean up TemplateContext implementation and add comprehensive docstrings

### 4. Context Builder with TemplateContext (TDD: Red-Green-Refactor)
- [ ] 4.1 **RED**: Create failing test for build_template_context() function signature
- [ ] 4.2 **GREEN**: Implement basic build_template_context() returning empty TemplateContext
- [ ] 4.3 **RED**: Create failing test for layered context creation (system → agent → project → collection → category → file)
- [ ] 4.4 **GREEN**: Implement context layering with TemplateContext.new_child()
- [ ] 4.5 **RED**: Create failing tests for datetime to ISO string conversion utilities
- [ ] 4.6 **GREEN**: Implement datetime conversion utilities
- [ ] 4.7 **RED**: Create failing tests for Path to string conversion utilities
- [ ] 4.8 **GREEN**: Implement Path conversion utilities
- [ ] 4.9 **RED**: Create failing tests for None value handling in context chain
- [ ] 4.10 **GREEN**: Implement graceful None handling
- [ ] 4.11 **REFACTOR**: Optimize context builder and add comprehensive error handling

### 5. Project Context Variables (TDD: Red-Green-Refactor)
- [ ] 5.1 **RED**: Create failing test for project context extraction from Project model
- [ ] 5.2 **GREEN**: Implement extract_project_context() function
- [ ] 5.3 **RED**: Create failing tests for project.name, created_at, updated_at
- [ ] 5.4 **GREEN**: Implement project basic fields extraction
- [ ] 5.5 **RED**: Create failing tests for project.categories list (category names)
- [ ] 5.6 **GREEN**: Implement categories list extraction
- [ ] 5.7 **RED**: Create failing tests for project.collections list (collection names)
- [ ] 5.8 **GREEN**: Implement collections list extraction
- [ ] 5.9 **RED**: Create failing test for missing project data handling
- [ ] 5.10 **GREEN**: Implement graceful handling of missing project data
- [ ] 5.11 **REFACTOR**: Clean up project context extractor

### 6. File Context Variables (TDD: Red-Green-Refactor)
- [ ] 6.1 **RED**: Create failing test for file context extraction from FileInfo
- [ ] 6.2 **GREEN**: Implement extract_file_context() function
- [ ] 6.3 **RED**: Create failing tests for file.path, basename, category, collection
- [ ] 6.4 **GREEN**: Implement file basic fields extraction
- [ ] 6.5 **RED**: Create failing test for file.size (rendered size for templates)
- [ ] 6.6 **GREEN**: Implement size field extraction
- [ ] 6.7 **RED**: Create failing tests for file.mtime, ctime (optional)
- [ ] 6.8 **GREEN**: Implement optional datetime fields extraction
- [ ] 6.9 **RED**: Create failing test for missing optional fields handling
- [ ] 6.10 **GREEN**: Implement graceful handling of missing optional fields
- [ ] 6.11 **REFACTOR**: Clean up file context extractor

### 7. Category Context Variables (TDD: Red-Green-Refactor)
- [ ] 7.1 **RED**: Create failing test for category context extraction from Category model
- [ ] 7.2 **GREEN**: Implement extract_category_context() function
- [ ] 7.3 **RED**: Create failing tests for category.name, description
- [ ] 7.4 **GREEN**: Implement category basic fields extraction
- [ ] 7.5 **RED**: Create failing test for category.dir (relative path only, security requirement)
- [ ] 7.6 **GREEN**: Implement secure relative path extraction
- [ ] 7.7 **RED**: Create failing test to ensure no docroot exposure
- [ ] 7.8 **GREEN**: Implement docroot exposure prevention
- [ ] 7.9 **RED**: Create failing test for security constraints validation
- [ ] 7.10 **GREEN**: Implement security validation
- [ ] 7.11 **REFACTOR**: Clean up category context extractor and security measures

### 8. Collection Context Variables (TDD: Red-Green-Refactor)
- [ ] 8.1 **RED**: Create failing test for collection context extraction from Collection model
- [ ] 8.2 **GREEN**: Implement extract_collection_context() function
- [ ] 8.3 **RED**: Create failing tests for collection.name, description
- [ ] 8.4 **GREEN**: Implement collection basic fields extraction
- [ ] 8.5 **RED**: Create failing test for collection.categories list
- [ ] 8.6 **GREEN**: Implement categories list extraction
- [ ] 8.7 **RED**: Create failing test for None handling when file not accessed via collection
- [ ] 8.8 **GREEN**: Implement None handling for collection context
- [ ] 8.9 **REFACTOR**: Clean up collection context extractor

### 9. Agent Context Variables (TDD: Red-Green-Refactor)
- [ ] 9.1 **RED**: Create failing test for agent context extraction from session
- [ ] 9.2 **GREEN**: Implement extract_agent_context() function
- [ ] 9.3 **RED**: Create failing test for @ variable (agent prompt character)
- [ ] 9.4 **GREEN**: Implement @ variable extraction
- [ ] 9.5 **RED**: Create failing tests for agent.name, version, prompt_prefix
- [ ] 9.6 **GREEN**: Implement agent info fields extraction
- [ ] 9.7 **RED**: Create failing test for missing agent info graceful handling
- [ ] 9.8 **GREEN**: Implement graceful handling of missing agent data
- [ ] 9.9 **REFACTOR**: Clean up agent context extractor

### 10. System Context Variables (TDD: Red-Green-Refactor)
- [ ] 10.1 **RED**: Create failing test for system context generation
- [ ] 10.2 **GREEN**: Implement extract_system_context() function
- [ ] 10.3 **RED**: Create failing test for now (ISO 8601 timestamp)
- [ ] 10.4 **GREEN**: Implement now timestamp generation
- [ ] 10.5 **RED**: Create failing test for timestamp (Unix timestamp)
- [ ] 10.6 **GREEN**: Implement Unix timestamp generation
- [ ] 10.7 **RED**: Create failing test for timestamp consistency within single render
- [ ] 10.8 **GREEN**: Implement timestamp consistency mechanism
- [ ] 10.9 **REFACTOR**: Clean up system context extractor and ensure consistency

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
