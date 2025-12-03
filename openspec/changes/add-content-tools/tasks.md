# Implementation Tasks

**See roadmap.md for overall strategy and phase dependencies**

## Phase 1: Core Content Retrieval (Category-Based)

### 1. Content Retrieval Logic
- [x] 1.1 Implement glob pattern matching (GUIDE-32 ✓)
- [x] 1.2 Implement file discovery in category directories (GUIDE-33 ✓)
- [x] 1.3 Implement file reading and content extraction (GUIDE-34 ✓)
- [x] 1.4 Add path resolution and validation (GUIDE-35 ✓)
- [x] 1.5 Handle missing files/directories errors (GUIDE-36 ✓)
- [x] 1.6 Add unit tests for pattern matching (GUIDE-32/37 ✓)
- [x] 1.7 Add unit tests for file operations (GUIDE-33/34/35/36/38 ✓)

### 2. MIME Multipart Formatting
- [x] 2.1 Implement single file formatter (plain markdown) (GUIDE-39 ✓)
- [x] 2.2 Implement MIME multipart formatter (RFC 2046) (GUIDE-40 ✓)
- [x] 2.3 Add metadata extraction (Content-Type, Content-Location, Content-Length) (GUIDE-41 ✓)
- [x] 2.4 Implement boundary generation (GUIDE-42 ✓)
- [x] 2.5 Add unit tests for single file format (GUIDE-43 ✓)
- [x] 2.6 Add unit tests for multipart format (GUIDE-44 ✓)
- [x] 2.7 Validate RFC 2046 compliance (GUIDE-45 ✓)

### 3. get_category_content Tool
- [x] 3.1 Define argument schema (category, pattern) (GUIDE-46 ✓)
- [x] 3.2 Implement tool function with session integration (GUIDE-47 ✓)
- [x] 3.3 Add Result pattern responses (GUIDE-48 ✓)
- [x] 3.4 Define error types (not_found, no_matches, file_read) (GUIDE-49 ✓)
- [x] 3.5 Add agent instructions for each error type (GUIDE-50 ✓)
- [x] 3.6 Register tool with MCP server (GUIDE-51 ✓)
- [x] 3.7 Add integration tests for tool (GUIDE-52 ✓)
- [x] 3.8 Test error cases and instructions (GUIDE-53 ✓)

## Phase 2: Template Support

### 4. Template Rendering
- [ ] 4.1 Add mustache library dependency
- [ ] 4.2 Implement .mustache file detection
- [ ] 4.3 Implement template rendering
- [ ] 4.4 Add pass-through for non-template files
- [ ] 4.5 Handle template syntax errors
- [ ] 4.6 Add unit tests for template detection
- [ ] 4.7 Add unit tests for rendering
- [ ] 4.8 Test error handling

### 5. Template Context Resolution
- [ ] 5.1 Define context sources (project, env, built-in)
- [ ] 5.2 Implement context priority and merging
- [ ] 5.3 Add built-in variables (project.name, timestamp, etc.)
- [ ] 5.4 Implement context resolver
- [ ] 5.5 Add unit tests for context resolution
- [ ] 5.6 Test context priority rules

### 6. Template Caching
- [ ] 6.1 Implement template cache structure
- [ ] 6.2 Add cache hit/miss logic
- [ ] 6.3 Implement cache invalidation on file changes
- [ ] 6.4 Add cache size limits and LRU eviction
- [ ] 6.5 Add unit tests for caching
- [ ] 6.6 Test cache invalidation
- [ ] 6.7 Performance testing

## PAUSE: Collection Management Tools

**External Dependency**: Switch to `add-collection-tools` implementation

Collection management tools must be implemented before Phase 3.

## Phase 3: Collection-Based Content Retrieval

### 7. get_collection_content Tool
- [ ] 7.1 Define argument schema (collection, pattern)
- [ ] 7.2 Implement collection resolution
- [ ] 7.3 Aggregate content from collection's categories
- [ ] 7.4 Apply pattern across all categories
- [ ] 7.5 Merge results with proper metadata
- [ ] 7.6 Add Result pattern responses
- [ ] 7.7 Register tool with MCP server
- [ ] 7.8 Add integration tests

### 8. get_content Tool (Unified Access)
- [ ] 8.1 Define argument schema (category_or_collection, pattern)
- [ ] 8.2 Implement category resolution (try first)
- [ ] 8.3 Implement collection resolution (fallback)
- [ ] 8.4 Add consistent error handling
- [ ] 8.5 Add agent-friendly error messages
- [ ] 8.6 Register tool with MCP server
- [ ] 8.7 Add integration tests
- [ ] 8.8 Test resolution priority

## Phase 4: Documentation

### 9. Documentation
- [ ] 9.1 Document tool usage and examples (content-tools.md)
- [ ] 9.2 Document pattern syntax guide
- [ ] 9.3 Document MIME multipart format
- [ ] 9.4 Document template syntax and context (content-templates.md)
- [ ] 9.5 Document context variables reference
- [ ] 9.6 Document caching behavior
- [ ] 9.7 Add troubleshooting guide (content-troubleshooting.md)
- [ ] 9.8 Document error types and solutions
- [ ] 9.9 Document agent instructions

## Summary

**Phase 1**: 3 task groups (Content Retrieval, MIME Formatting, get_category_content)
**Phase 2**: 3 task groups (Template Rendering, Context Resolution, Caching)
**Phase 3**: 2 task groups (get_collection_content, get_content)
**Phase 4**: 1 task group (Documentation)

**Total**: 9 task groups, ~60 individual tasks
