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
