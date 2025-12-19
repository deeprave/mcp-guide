# Implementation Tasks: Guide Pattern Enhancement

**Approval gate**: PENDING

## Status

**Status:** Proposed - Not Started

## Phase 1: Foundation (Slash Syntax)

### 1.1 Core Infrastructure
- [ ] 1.1.1 Create DocumentExpression model for unified parsing
- [ ] 1.1.2 Implement two-tier category name validation (parsing vs creation)
- [ ] 1.1.3 Fix `Result.ok()` method signature to accept optional value parameter
- [ ] 1.1.4 Extract gather_category_fileinfos function from existing category content logic
- [ ] 1.1.5 Extract render_fileinfos function from existing rendering logic
- [ ] 1.1.6 Refactor internal_category_content to use common functions
- [ ] 1.1.7 Implement gather_content function using gather_category_fileinfos
- [ ] 1.1.8 Refactor get_content to use gather_content and render_fileinfos
- [ ] 1.1.9 Implement slash syntax parsing using DocumentExpression
- [ ] 1.1.10 Add validation for slash syntax edge cases
- [ ] 1.1.11 Update error handling to be consistent across all content retrieval

### 1.2 Testing & Validation
- [ ] 1.2.1 Add unit tests for slash syntax parsing
- [ ] 1.2.2 Add integration tests for `get_content` with slash syntax
- [ ] 1.2.3 Verify backward compatibility with existing two-parameter calls
- [ ] 1.2.4 Test edge cases (multiple slashes, empty patterns, etc.)

## Phase 2: Multi-Pattern Support

### 2.1 Pattern Processing
- [ ] 2.1.1 Implement `+` separator parsing for multiple patterns
- [ ] 2.1.2 Extend pattern matching to handle pattern lists
- [ ] 2.1.3 Add pattern aggregation logic for multiple matches
- [ ] 2.1.4 Implement pattern validation for multi-pattern syntax

### 2.2 Integration
- [ ] 2.2.1 Integrate multi-pattern support with slash syntax
- [ ] 2.2.2 Update category content retrieval to handle pattern lists
- [ ] 2.2.3 Ensure consistent behavior across all pattern types

### 2.3 Testing
- [ ] 2.3.1 Add unit tests for multi-pattern parsing
- [ ] 2.3.2 Add integration tests for multi-pattern content retrieval
- [ ] 2.3.3 Test pattern validation and error handling

## Phase 3: Expression Parsing

### 3.1 Expression Parser
- [ ] 3.1.1 Create expression parser module
- [ ] 3.1.2 Implement comma-separated expression parsing
- [ ] 3.1.3 Add precedence rules for operators (`,` and `+`)
- [ ] 3.1.4 Implement whitespace handling and trimming
- [ ] 3.1.5 Add comprehensive error reporting for malformed expressions

### 3.2 Content Aggregation
- [ ] 3.2.1 Implement multi-category content aggregation
- [ ] 3.2.2 Add result deduplication logic
- [ ] 3.2.3 Maintain content ordering and metadata
- [ ] 3.2.4 Handle partial failures gracefully

### 3.3 Testing
- [ ] 3.3.1 Add unit tests for expression parser
- [ ] 3.3.2 Add integration tests for multi-category expressions
- [ ] 3.3.3 Test complex expression combinations
- [ ] 3.3.4 Test error handling and edge cases

## Phase 4: Collection Enhancement

### 4.1 Data Model Extension
- [ ] 4.1.1 Extend `Collection` model to support pattern overrides
- [ ] 4.1.2 Update YAML serialization/deserialization
- [ ] 4.1.3 Add validation for pattern overrides
- [ ] 4.1.4 Implement backward compatibility for existing collections

### 4.2 Pattern Resolution
- [ ] 4.2.1 Implement three-tier pattern resolution logic
- [ ] 4.2.2 Update collection content retrieval to use pattern overrides
- [ ] 4.2.3 Add pattern override precedence handling
- [ ] 4.2.4 Ensure consistent behavior across all scenarios

### 4.3 Collection Management Tools
- [ ] 4.3.1 Update `collection_add` to support pattern overrides
- [ ] 4.3.2 Update `collection_change` to handle pattern overrides
- [ ] 4.3.3 Update `collection_update` to modify pattern overrides
- [ ] 4.3.4 Update `collection_list` to display pattern overrides

### 4.4 Testing
- [ ] 4.4.1 Add unit tests for Collection model changes
- [ ] 4.4.2 Add integration tests for pattern override resolution
- [ ] 4.4.3 Test collection management tools with overrides
- [ ] 4.4.4 Test backward compatibility with existing collections

## Phase 5: Tool Consolidation

### 5.1 Unified Content Access
- [ ] 5.1.1 Implement collection resolution in `get_content`
- [ ] 5.1.2 Add collection vs category name resolution logic
- [ ] 5.1.3 Support mixed collection/category expressions
- [ ] 5.1.4 Ensure performance equivalent to separate tools

### 5.2 Deprecation Management
- [ ] 5.2.1 Add deprecation warnings to `get_collection_content`
- [ ] 5.2.2 Create migration documentation and examples
- [ ] 5.2.3 Update tool documentation to recommend `get_content`
- [ ] 5.2.4 Plan removal timeline for deprecated tool

### 5.3 Final Integration
- [ ] 5.3.1 Comprehensive integration testing across all phases
- [ ] 5.3.2 Performance testing and optimization
- [ ] 5.3.3 Documentation updates for unified API
- [ ] 5.3.4 User migration guide and examples

## Validation & Quality Assurance

### Cross-Phase Testing
- [ ] End-to-end testing of complete feature set
- [ ] Backward compatibility verification
- [ ] Performance regression testing
- [ ] User acceptance testing with real scenarios

### Documentation
- [ ] Update tool documentation with new syntax
- [ ] Create migration guide from old to new syntax
- [ ] Add examples for all supported expression types
- [ ] Update README with unified content access patterns
