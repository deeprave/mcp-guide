# Phase 3: Collection-Based Content Retrieval - Task Breakdowns

**Note**: This phase requires collection management tools to be implemented first (add-collection-tools).

**UPDATED 2025-12-05**: Corrected get_content semantics and added FileInfo metadata enhancements.

## Key Semantic Changes for Task 8 (get_content)

**Original (INCORRECT):**
- Try category first, fallback to collection if not found
- Return first match

**Corrected (CORRECT):**
- Search collections first, then categories (BOTH, not either/or)
- Aggregate all FileInfo from both searches
- De-duplicate by absolute path, preserving discovery order
- First occurrence wins (collection metadata over category-only)
- Read content for unique files
- Return aggregated result

## FileInfo Metadata Enhancement (Applies to All Tasks)

Two new fields added to FileInfo for future templating support:
- `category: Optional[str] = None` - category where file was discovered
- `collection: Optional[str] = None` - collection where file was discovered

**Field Population:**
- get_category_content: Set `category` field after discovery
- get_collection_content: Set both `category` and `collection` fields after discovery
- get_content: Fields already set by underlying category searches

## Consistency Fix (Task 7.x)

get_collection_content must add instruction field when no files found:
- Change: `Result.ok(message)` → `Result.ok(message)` + `result.instruction = INSTRUCTION_PATTERN_ERROR`
- Ensures consistency with get_category_content behavior

## Task 7.1: Define Argument Schema (collection, pattern)

**Description**: Define Pydantic argument schema for get_collection_content tool following ADR-008 conventions.

**Requirements**:
- Inherit from ToolArguments base class
- Define `collection` (required, string) - collection ID
- Define `pattern` (optional, string)
- Add field descriptions
- Add validation

**Assumptions**:
- ToolArguments base class exists
- Collection IDs are strings
- Pattern validation reuses existing logic

**Acceptance Criteria**:
- [ ] Schema class inherits from ToolArguments
- [ ] `collection` field is required string
- [ ] `pattern` field is optional string
- [ ] Field descriptions are clear
- [ ] Schema validates correctly
- [ ] Schema generates proper markdown docs
- [ ] Unit tests verify schema validation

---

## Task 7.2: Implement Collection Resolution

**Description**: Implement collection resolution from project configuration by collection ID.

**Requirements**:
- Get project from session
- Look up collection by ID
- Return collection object
- Handle missing collection

**Assumptions**:
- Collection management tools provide collection model
- Collections have unique IDs
- Project config contains collections

**Acceptance Criteria**:
- [ ] Resolves collection by ID
- [ ] Returns collection object
- [ ] Returns None for missing collection
- [ ] Handles empty collection list
- [ ] Unit tests verify resolution
- [ ] Unit tests verify error cases

---

## Task 7.3: Aggregate Content from Collection's Categories

**Description**: Implement content aggregation that retrieves content from all categories in a collection.

**Requirements**:
- Get categories from collection
- Retrieve content from each category
- Use category's default patterns or override
- Collect all results
- Preserve category context

**Assumptions**:
- Collection contains list of category names
- Categories exist in project config
- Content retrieval logic is reusable

**Acceptance Criteria**:
- [ ] Iterates through collection's categories
- [ ] Retrieves content from each category
- [ ] Uses default patterns per category
- [ ] Collects all results
- [ ] Preserves category name in metadata
- [ ] Handles missing categories gracefully
- [ ] Unit tests verify aggregation

---

## Task 7.4: Apply Pattern Across All Categories

**Description**: Implement pattern override that applies same pattern to all categories in collection.

**Requirements**:
- Accept optional pattern parameter
- Override category default patterns
- Apply pattern to all categories
- Collect matching results

**Assumptions**:
- Pattern applies uniformly
- Pattern syntax is same for all categories
- Override is complete (no mixing with defaults)

**Acceptance Criteria**:
- [ ] Pattern overrides all category defaults
- [ ] Same pattern applied to each category
- [ ] Results collected from all categories
- [ ] Empty results handled gracefully
- [ ] Unit tests verify pattern override
- [ ] Unit tests verify default pattern behavior

---

## Task 7.5: Merge Results with Proper Metadata

**Description**: Implement result merging that combines content from multiple categories with proper metadata.

**Requirements**:
- Combine results from all categories
- Preserve category context in metadata
- Use MIME multipart for multiple files
- Include Content-Location with category info
- Handle single vs multiple results

**Assumptions**:
- MIME multipart formatter is reusable
- Metadata includes category name
- Content-Location format: `guide://collection/{id}/category/{name}/{file}`

**Acceptance Criteria**:
- [ ] Merges results from all categories
- [ ] Single file returns plain markdown
- [ ] Multiple files return MIME multipart
- [ ] Content-Location includes collection and category
- [ ] Metadata preserves category context
- [ ] Unit tests verify merging
- [ ] Unit tests verify metadata format

---

## Task 7.6: Add Result Pattern Responses

**Description**: Implement Result pattern responses for get_collection_content tool.

**Requirements**:
- Use Result.ok() for success
- Use Result.failure() for errors
- Include aggregated content in value
- Include error details in failures
- Return JSON string

**Assumptions**:
- Result pattern is established
- Error types are defined
- JSON format is MCP-compatible

**Acceptance Criteria**:
- [ ] Success returns Result.ok(content).to_json_str()
- [ ] Failures return Result.failure(...).to_json_str()
- [ ] Success includes aggregated content
- [ ] Failures include error_type
- [ ] Failures include agent instruction
- [ ] JSON format is valid
- [ ] Unit tests verify response formats

---

## Task 7.7: Register Tool with MCP Server

**Description**: Register get_collection_content tool with MCP server using tool decorator.

**Requirements**:
- Use @tools.tool(ArgsClass) decorator
- Tool appears in MCP tool list
- Tool schema is correct
- Tool is callable via MCP

**Assumptions**:
- Tool registration infrastructure exists
- Decorator handles registration
- MCP server is running

**Acceptance Criteria**:
- [ ] Tool decorated with @tools.tool(CollectionContentArgs)
- [ ] Tool appears in server tool list
- [ ] Tool schema matches argument class
- [ ] Tool description is clear
- [ ] Tool is callable via MCP protocol
- [ ] Integration test verifies registration
- [ ] Integration test verifies tool call

---

## Task 7.8: Add Integration Tests

**Description**: Create integration tests for get_collection_content tool.

**Requirements**:
- Test tool via MCP protocol
- Test with real project configuration
- Test success and error cases
- Verify Result pattern responses
- Test content aggregation

**Assumptions**:
- Integration test infrastructure exists
- Test projects can be created
- Collections can be configured

**Acceptance Criteria**:
- [ ] Test successful content retrieval
- [ ] Test with default patterns
- [ ] Test with override pattern
- [ ] Test collection not found error
- [ ] Test no matches error
- [ ] Test aggregation from multiple categories
- [ ] All tests pass
- [ ] Tests verify JSON response format

---

## Task 8.1: Define Argument Schema (category_or_collection, pattern)

**Description**: Define Pydantic argument schema for get_content tool (unified access).

**CORRECTED**: Collections searched first, then categories (BOTH, not either/or).

**Requirements**:
- Inherit from ToolArguments base class
- Define `category_or_collection` (required, string) - exact name match
- Define `pattern` (optional, string) - file pattern override
- Add field descriptions
- Add validation

**Assumptions**:
- ToolArguments base class exists
- Name matches exact collection or category name
- Both collections and categories are searched (not fallback)

**Acceptance Criteria**:
- [ ] Schema class inherits from ToolArguments
- [ ] `category_or_collection` field is required string
- [ ] `pattern` field is optional string
- [ ] Field descriptions explain aggregation behavior
- [ ] Schema validates correctly
- [ ] Schema generates proper markdown docs
- [ ] Unit tests verify schema validation

---

## Task 8.2: Implement Collection Search (First)

**Description**: Implement collection search as first step in unified access.

**CORRECTED**: Collections searched first (not category first).

**Requirements**:
- Search for collection with exact name match
- If found: aggregate files from all categories in collection
- Set `file.category` and `file.collection` fields
- Apply pattern override to all categories (or use defaults)
- Collect all FileInfo

**Assumptions**:
- Collection names are unique
- Collection search is fast
- Collections searched before categories

**Acceptance Criteria**:
- [ ] Searches collection by exact name match first
- [ ] Aggregates files from all categories in collection
- [ ] Sets both category and collection fields on FileInfo
- [ ] Applies pattern override correctly
- [ ] Collects all FileInfo for later de-duplication
- [ ] Unit tests verify collection search
- [ ] Unit tests verify metadata population
- [ ] Returns None if not found
- [ ] No error on miss
- [ ] Unit tests verify resolution
- [ ] Unit tests verify priority

---

## Task 8.3: Implement Category Search (Second)

**Description**: Implement category search as second step in unified access.

**CORRECTED**: Categories searched after collections (NOT fallback - always search both).

**Requirements**:
- Search for category with exact name match
- If found: discover files using pattern override (or defaults)
- `file.category` already set by discovery
- Collect all FileInfo for aggregation

**Assumptions**:
- Category names are unique
- Category search is fast
- Categories searched after collections (both are searched)

**Acceptance Criteria**:
- [ ] Searches category by exact name match
- [ ] Discovers files with pattern override
- [ ] Category field already set on FileInfo
- [ ] Collects all FileInfo for later de-duplication
- [ ] Unit tests verify category search
- [ ] Unit tests verify it runs after collection search

---

## Task 8.4: Implement De-duplication and Aggregation

**Description**: Implement de-duplication of FileInfo by absolute path and content aggregation.

**CORRECTED**: De-duplicate before reading content (efficiency).

**Requirements**:
- De-duplicate FileInfo by absolute path (category_dir / file.path)
- Preserve discovery order (collections first, then categories)
- First occurrence wins (collection metadata preserved)
- Read content for unique files only
- Format and return aggregated content

**Assumptions**:
- FileInfo.path is relative to category_dir
- Absolute path uniquely identifies a file
- First occurrence has most complete metadata

**Acceptance Criteria**:
- [ ] De-duplicates by absolute file path
- [ ] Preserves discovery order
- [ ] First occurrence wins
- [ ] Reads content only for unique files
- [ ] Formats aggregated content correctly
- [ ] Unit tests verify de-duplication logic
- [ ] Unit tests verify metadata preservation

---

## Task 8.5: Implement Consistent Empty Results Handling

**Description**: Implement consistent empty results behavior across all content tools.

**CORRECTED**: Empty results return success with instruction (not error).

**Requirements**:
- Return `Result.ok()` when no files found
- Set `result.instruction = INSTRUCTION_PATTERN_ERROR`
- Use consistent message format
- Match get_collection_content behavior

**Assumptions**:
- Empty results are not errors
- Agent needs instruction not to retry
- Consistency across tools is important

**Acceptance Criteria**:
- [ ] Returns `Result.ok()` for empty results
- [ ] Sets instruction field to INSTRUCTION_PATTERN_ERROR
- [ ] Message format is consistent
- [ ] Works when no collection or category matches
- [ ] Works when matches found but no files
- [ ] Unit tests verify empty result handling

---

## Task 8.6: Register Tool with MCP Server

**Description**: Register get_content tool with MCP server using tool decorator.

**Requirements**:
- Use @tools.tool(ArgsClass) decorator
- Tool appears in MCP tool list
- Tool schema is correct
- Tool is callable via MCP

**Assumptions**:
- Tool registration infrastructure exists
- Decorator handles registration
- MCP server is running

**Acceptance Criteria**:
- [ ] Tool decorated with @tools.tool(ContentArgs)
- [ ] Tool appears in server tool list
- [ ] Tool schema matches argument class
- [ ] Tool description explains unified access
- [ ] Tool is callable via MCP protocol
- [ ] Integration test verifies registration
- [ ] Integration test verifies tool call

---

## Task 8.7: Add Integration Tests

**Description**: Create integration tests for get_content tool (unified access).

**CORRECTED**: Test aggregation from both collections and categories.

**Requirements**:
- Test tool via MCP protocol
- Test collection search
- Test category search
- Test aggregation from both
- Test de-duplication
- Test error cases

**Assumptions**:
- Integration test infrastructure exists
- Test projects can be created
- Both categories and collections can be configured

**Acceptance Criteria**:
- [ ] Test collection-only match
- [ ] Test category-only match
- [ ] Test both match (aggregation and de-duplication)
- [ ] Test neither match (empty result)
- [ ] Test with pattern override
- [ ] Test FileInfo metadata population
- [ ] All tests pass
- [ ] Tests verify JSON response format

---

## Task 8.8: Test De-duplication Priority

**Description**: Create tests that verify collection-first de-duplication priority.

**CORRECTED**: Collections searched first, so collection metadata wins on duplicates.

**Requirements**:
- Test with file in collection only
- Test with file in category only
- Test with same file in both
- Verify collection metadata wins when both match

**Assumptions**:
- Same file can appear in collection and category
- De-duplication is by absolute path
- First occurrence (collection) wins

**Acceptance Criteria**:
- [ ] Test file in collection only
- [ ] Test file in category only
- [ ] Test same file in both (collection metadata wins)
- [ ] Test multiple duplicates across categories
- [ ] Verify de-duplication by absolute path
- [ ] Verify metadata preservation
- [ ] All tests pass
