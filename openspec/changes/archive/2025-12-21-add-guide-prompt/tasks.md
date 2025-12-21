## 1. Core Infrastructure
- [x] 1.1 Create `PromptArguments` protocol in `mcp_core/prompt_arguments.py`
- [x] 1.2 Create `GuidePromptArguments` class with command and arguments fields
- [x] 1.3 Add prompt decorator infrastructure to `mcp_core/prompt_decorator.py`
- [x] 1.4 Create prompt proxy pattern similar to tools proxy in server.py

## 2. Guide Prompt Implementation
- [x] 2.1 Create `guide_prompt.py` with `@guide` prompt handler
- [x] 2.2 Implement MVP logic to call existing `get_content` tool directly
- [x] 2.3 Add prompt registration to server.py
- [x] 2.4 Handle empty/missing command gracefully

## 3. Integration & Testing
- [x] 3.1 Add unit tests for `PromptArguments` and `GuidePromptArguments`
- [x] 3.2 Add unit tests for prompt decorator infrastructure
- [x] 3.3 Add integration tests for `@guide` prompt with various argument patterns
- [x] 3.4 Test prompt registration and server initialization

## 4. Documentation
- [x] 4.1 Update server spec with prompt support requirements
- [x] 4.2 Document prompt argument patterns and usage examples

## Implementation Notes

**Architecture Changes Made:**
- Created `Arguments` base class instead of separate `PromptArguments` protocol
- Used package aliases (`ToolArguments`, `PromptArguments`) for semantic clarity
- Refactored existing `ToolArguments` to use common base class
- No breaking changes to existing tool implementations

**Key Files Created:**
- `src/mcp_core/arguments.py` - Common Arguments base class
- `src/mcp_core/prompt_decorator.py` - Prompt decorator with MCP_PROMPT_PREFIX support
- `src/mcp_guide/prompts/guide_prompt.py` - @guide prompt implementation
- `src/mcp_guide/prompts/guide_prompt_args.py` - GuidePromptArguments class

**Testing Coverage:**
- Unit tests for Arguments base class (refactored from ToolArguments tests)
- Unit tests for prompt decorator (prefix handling, schema generation)
- Integration tests for @guide prompt (various scenarios, error handling)
- Alias tests for backward compatibility

**Usage Examples:**
- `@guide guide` - Get content from 'guide' category
- `@guide lang/python` - Get content matching 'lang/python' pattern
- `@guide` - Get help message

All tasks completed successfully. The @guide prompt is ready for production use.

---

## 5. MCP Compatibility Refactor (NEW)
- [x] 5.1 Remove `GuidePromptArguments` class from `guide_prompt_args.py`
- [x] 5.2 Delete `guide_prompt_args.py` file entirely
- [x] 5.3 Update imports in `guide_prompt.py` to remove argument class dependency
- [x] 5.4 Clean up any unused prompt argument infrastructure

## 6. Implement MCP-Compatible Argument Handling (NEW)
- [x] 6.1 Replace prompt function signature with direct parameters (arg1-argF)
- [x] 6.2 Implement argv-style parsing: ["guide", arg1, arg2, ...] stopping at None
- [x] 6.3 Add parameter validation and help message for empty arguments
- [x] 6.4 Update prompt decorator to use direct function parameters

## 7. MVP Content Access Implementation (NEW)
- [x] 7.1 Process first argument (arg1) as category/pattern for get_content
- [x] 7.2 Handle empty arguments with usage help message
- [x] 7.3 Reserve remaining arguments (arg2-argF) for future click integration
- [x] 7.4 Maintain backward compatibility with existing content access patterns

## 8. Testing & Validation (NEW)
- [x] 8.1 Update existing prompt tests to use new argument format
- [x] 8.2 Add tests for argv parsing logic (None handling, argument ordering)
- [x] 8.3 Test various argument patterns: single, multiple, empty
- [x] 8.4 Verify MCP client compatibility with space-separated arguments

## 9. Documentation Updates (NEW)
- [x] 9.1 Update prompt usage examples in docstrings
- [x] 9.2 Document argv parsing behavior and limitations
- [x] 9.3 Add examples for future click integration approach

## MCP Compatibility Notes

**Key Changes Required:**
- Remove complex `GuidePromptArguments` class due to MCP limitations
- Use 15 optional string parameters (arg1-arg9, argA-argF) for variable arguments
- Implement argv-style parsing with None-termination
- Reserve arguments for future click command-line processing

**MCP Compatibility:**
- MCP clients parse space-separated arguments into individual parameters
- FastMCP doesn't support `*args` or `**kwargs` for prompts
- Fixed parameter count is the only viable solution for variable arguments

**Usage Examples:**
- `@guide lang/python` → argv = ["guide", "lang/python"]
- `@guide lang/python advanced` → argv = ["guide", "lang/python", "advanced"]
- `@guide` → argv = ["guide"] (help message)

**Future Extensibility:**
- argv list ready for click command-line parsing framework
- Arguments beyond arg1 reserved for advanced features
- Clean separation between argument parsing and content processing
