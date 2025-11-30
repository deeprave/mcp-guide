# Phase 3: Collection-Based Content Retrieval - Task Breakdowns

**Note**: This phase requires collection management tools to be implemented first (add-collection-tools).

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

**Requirements**:
- Inherit from ToolArguments base class
- Define `category_or_collection` (required, string)
- Define `pattern` (optional, string)
- Add field descriptions
- Add validation

**Assumptions**:
- ToolArguments base class exists
- Name can be category or collection ID
- Ambiguity resolved by trying category first

**Acceptance Criteria**:
- [ ] Schema class inherits from ToolArguments
- [ ] `category_or_collection` field is required string
- [ ] `pattern` field is optional string
- [ ] Field descriptions explain resolution order
- [ ] Schema validates correctly
- [ ] Schema generates proper markdown docs
- [ ] Unit tests verify schema validation

---

## Task 8.2: Implement Category Resolution (Try First)

**Description**: Implement category resolution as first attempt in unified access.

**Requirements**:
- Try to resolve as category name
- Return category if found
- Return None if not found
- Don't error on miss (try collection next)

**Assumptions**:
- Category names are unique
- Category resolution is fast
- Categories tried before collections

**Acceptance Criteria**:
- [ ] Attempts category resolution first
- [ ] Returns category if found
- [ ] Returns None if not found
- [ ] No error on miss
- [ ] Unit tests verify resolution
- [ ] Unit tests verify priority

---

## Task 8.3: Implement Collection Resolution (Fallback)

**Description**: Implement collection resolution as fallback when category not found.

**Requirements**:
- Try collection resolution if category not found
- Return collection if found
- Return None if not found
- Error if neither found

**Assumptions**:
- Collection IDs are unique
- Collection resolution is fast
- Collections tried after categories

**Acceptance Criteria**:
- [ ] Attempts collection resolution on category miss
- [ ] Returns collection if found
- [ ] Returns None if not found
- [ ] Errors if neither category nor collection found
- [ ] Unit tests verify fallback
- [ ] Unit tests verify error case

---

## Task 8.4: Add Consistent Error Handling

**Description**: Implement consistent error handling for unified access tool.

**Requirements**:
- Handle not found (neither category nor collection)
- Handle no matches
- Handle no session
- Use same error types as other tools
- Include agent instructions

**Assumptions**:
- Error types are defined
- Error messages are consistent
- Agent instructions are established

**Acceptance Criteria**:
- [ ] `not_found` when neither found
- [ ] `no_matches` when pattern matches nothing
- [ ] `no_session` when no project context
- [ ] Error messages are clear
- [ ] Agent instructions included
- [ ] Unit tests verify all error types

---

## Task 8.5: Add Agent-Friendly Error Messages

**Description**: Implement clear, actionable error messages for unified access tool.

**Requirements**:
- Explain what was tried (category, then collection)
- Suggest corrective actions
- Include specific details
- Follow established message patterns

**Assumptions**:
- Users may not know if name is category or collection
- Error messages should educate
- Suggestions should be actionable

**Acceptance Criteria**:
- [ ] Error explains resolution attempt order
- [ ] Error suggests checking category list
- [ ] Error suggests checking collection list
- [ ] Error includes the name that was tried
- [ ] Messages are user-friendly
- [ ] Unit tests verify message content

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

**Requirements**:
- Test tool via MCP protocol
- Test category resolution
- Test collection resolution
- Test resolution priority
- Test error cases

**Assumptions**:
- Integration test infrastructure exists
- Test projects can be created
- Both categories and collections can be configured

**Acceptance Criteria**:
- [ ] Test category resolution (found)
- [ ] Test collection resolution (fallback)
- [ ] Test resolution priority (category first)
- [ ] Test not found error
- [ ] Test no matches error
- [ ] Test with pattern override
- [ ] All tests pass
- [ ] Tests verify JSON response format

---

## Task 8.8: Test Resolution Priority

**Description**: Create tests that verify category-first resolution priority.

**Requirements**:
- Test with name that matches category
- Test with name that matches collection
- Test with name that matches both
- Verify category wins when both match

**Assumptions**:
- Names can overlap (category and collection)
- Priority is deterministic
- Tests can create overlapping names

**Acceptance Criteria**:
- [ ] Test category-only match
- [ ] Test collection-only match
- [ ] Test both match (category wins)
- [ ] Test neither match (error)
- [ ] Verify resolution order in logs
- [ ] All tests pass
