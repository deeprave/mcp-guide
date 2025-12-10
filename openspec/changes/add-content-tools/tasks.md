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

## Phase 2: Collection-Based Content Retrieval

**UPDATED 2025-12-05**: Corrected get_content semantics and added FileInfo metadata enhancements.

**FileInfo Enhancement**: Add `category` and `collection` optional fields for future templating support.

### 4. get_collection_content Tool
- [x] 4.1 Define argument schema (collection, pattern) (GUIDE-75 ✓)
- [x] 4.2 Implement collection resolution (GUIDE-76 ✓)
- [x] 4.3 Aggregate content from collection's categories (GUIDE-77 ✓)
- [x] 4.4 Apply pattern across all categories (GUIDE-78 ✓)
- [x] 4.5 Merge results with proper metadata (GUIDE-79 ✓)
- [x] 4.6 Add Result pattern responses (GUIDE-80 ✓)
- [x] 4.7 Register tool with MCP server (GUIDE-81 ✓)
- [x] 4.8 Add integration tests (GUIDE-82 ✓)
- [x] 4.9 Add FileInfo metadata (category, collection fields) ✓
- [x] 4.10 Fix empty results (add instruction field) ✓

### 5. get_content Tool (Unified Access)
**CORRECTED**: Collections searched first, then categories (BOTH, not either/or). Aggregate and de-duplicate.

- [x] 5.1 Define argument schema (category_or_collection, pattern) (GUIDE-83 ✓)
- [x] 5.2 Implement collection search (first) (GUIDE-84 ✓)
- [x] 5.3 Implement category search (second) (GUIDE-85 ✓)
- [x] 5.4 Implement de-duplication and aggregation (GUIDE-86 ✓)
- [x] 5.5 Implement consistent empty results handling (GUIDE-87 ✓)
- [x] 5.6 Register tool with MCP server (GUIDE-88 ✓)
- [x] 5.7 Add integration tests (GUIDE-89 ✓)
- [x] 5.8 Test de-duplication priority (GUIDE-90 ✓)

## Phase 3: Documentation

### 6. Documentation (CONSOLIDATED)
- [x] 6.1 Document tool usage and examples → docs/content-tools.md ✓
- [x] 6.2 Document pattern syntax guide → docs/content-tools.md ✓
- [x] 6.3 Document MIME multipart format → docs/content-tools.md ✓
- [x] 6.4 Document error types and solutions → docs/content-tools.md ✓
- [x] 6.5 Document agent instructions → docs/content-tools.md ✓
- [x] 6.6 Consolidated into single comprehensive document ✓

**Note**: All documentation consolidated into `docs/content-tools.md` for brevity and practicality.

## Summary

**Phase 1**: 3 task groups (Content Retrieval, MIME Formatting, get_category_content) ✅
**Phase 2**: 2 task groups (get_collection_content, get_content) ✅
**Phase 3**: 1 task group (Documentation) ✅

**Total**: 6 task groups, ~40 individual tasks - **100% COMPLETE**

**Note**: Template rendering and context resolution moved to separate `template-support` feature.

**Ready for archiving**: All functionality implemented, tested, and documented.
