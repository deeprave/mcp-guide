# Content Tools Implementation Roadmap

## Overview

This roadmap outlines the phased implementation of content retrieval tools. The implementation is split into phases that can be interleaved with collection management tools development.

## Implementation Strategy

Content tools and collection management tools will be developed in parallel:
1. Implement core content retrieval for categories
2. **PAUSE** - Implement collection management tools
3. Resume content tools for collection-based retrieval
4. Complete with documentation

## Phase 1: Core Content Retrieval (Category-Based)

**Goal**: Implement `get_category_content` with basic file serving

### Phase 1.1: Content Retrieval Logic
- Glob pattern matching for file discovery
- File reading and content extraction
- Path resolution within category directories
- Error handling for missing files/directories

### Phase 1.2: MIME Multipart Formatting
- Single file response (plain markdown)
- Multiple file response (MIME multipart/mixed)
- Metadata extraction (Content-Type, Content-Location, Content-Length)
- RFC 2046 compliant formatting

### Phase 1.3: get_category_content Tool
- Tool argument schema (category name, optional pattern)
- Session integration for project context
- Result pattern responses
- Error types: not_found, no_matches, no_session
- Agent instructions for each error type

**Deliverables**:
- Content retrieval module
- MIME formatter module
- get_category_content tool
- Unit tests for all components
- Integration tests for tool

**Dependencies**: None (uses existing infrastructure)

## Phase 2: Template Support (Optional Files)

**Goal**: Add mustache template rendering for .mustache files

### Phase 2.1: Template Rendering
- Detect .mustache file extensions
- Render templates using mustache library
- Pass through non-template files unchanged
- Error handling for template syntax errors

### Phase 2.2: Template Context Resolution
- Define context sources (project config, environment, etc.)
- Context priority and merging rules
- Built-in context variables
- Custom context providers

### Phase 2.3: Template Caching
- Cache parsed templates
- Cache invalidation on file changes
- Memory management for cache
- Performance optimization

**Deliverables**:
- Template renderer module
- Context resolver module
- Template cache implementation
- Tests for template rendering and caching

**Dependencies**: Phase 1 complete

## PAUSE: Collection Management Tools

**External Dependency**: Switch to `add-collection-tools` implementation

Collection management tools must be implemented before Phase 3:
- collection_list
- collection_add
- collection_remove
- collection_change
- collection_update

**Rationale**: `get_collection_content` requires collection management infrastructure

## Phase 3: Collection-Based Content Retrieval

**Goal**: Implement collection content aggregation

### Phase 3.1: get_collection_content Tool
- Tool argument schema (collection ID, optional pattern)
- Aggregate content from collection's categories
- Apply pattern across all categories
- Merge results with proper metadata
- Result pattern responses

### Phase 3.2: get_content Tool (Unified Access)
- Try category resolution first
- Fall back to collection resolution
- Consistent error handling
- Agent-friendly error messages

**Deliverables**:
- get_collection_content tool
- get_content tool
- Integration tests for collection-based retrieval
- Tests for unified access

**Dependencies**:
- Phase 1 complete
- Phase 2 complete
- Collection management tools complete

## Phase 4: Documentation

**Goal**: Comprehensive documentation for all content tools

### Phase 4.1: Tool Usage Documentation
- Examples for each tool
- Common workflows
- Pattern syntax guide
- MIME multipart format explanation

### Phase 4.2: Template Documentation
- Template syntax (mustache)
- Context variables reference
- Custom context providers
- Caching behavior

### Phase 4.3: Troubleshooting Guide
- Error types and solutions
- Agent instructions explanation
- Common issues and fixes
- Performance considerations

**Deliverables**:
- docs/tools/content-tools.md
- docs/tools/content-templates.md
- docs/tools/content-troubleshooting.md

**Dependencies**: All phases complete

## Future Considerations

### Agent Filesystem Access (Future Task)

**Note**: Not part of current scope, but worth documenting for future planning.

**Goal**: Allow agents to serve files from their local filesystem

**Use Case**: Users create local instruction files that agents can reference

**Considerations**:
- Security: Path traversal prevention
- Permissions: Read-only access
- Discovery: How agents advertise available files
- Protocol: URI scheme for agent files (agent://?)
- Coordination: Agent-server communication protocol

**Recommendation**: Create separate task/proposal when collection tools are complete

## Task Breakdown

### Phase 1 Tasks (Immediate)
1. Content retrieval logic implementation plan
2. MIME multipart formatting implementation plan
3. get_category_content tool implementation plan

### Phase 2 Tasks (After Phase 1)
4. Template rendering implementation plan
5. Template context resolution implementation plan
6. Template caching implementation plan

### Phase 3 Tasks (After Collection Tools)
7. get_collection_content tool implementation plan
8. get_content tool implementation plan

### Phase 4 Tasks (Final)
9. Documentation implementation plan

## Timeline Estimate

- **Phase 1**: 3-4 implementation cycles
- **Phase 2**: 2-3 implementation cycles
- **PAUSE**: Collection tools (separate roadmap)
- **Phase 3**: 2 implementation cycles
- **Phase 4**: 1 implementation cycle

**Total**: ~8-10 cycles for content tools (excluding collection tools pause)

## Success Criteria

- ✅ All three tools implemented and tested
- ✅ Template rendering works for .mustache files
- ✅ MIME multipart format compliant with RFC 2046
- ✅ Result pattern used consistently
- ✅ Agent instructions prevent futile remediation
- ✅ Documentation complete and accurate
- ✅ 90%+ test coverage on new code
- ✅ All quality checks pass (ruff, mypy, pytest)
