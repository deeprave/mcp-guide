## 1. Remove Complex Argument Infrastructure
- [ ] 1.1 Remove `GuidePromptArguments` class from `guide_prompt_args.py`
- [ ] 1.2 Delete `guide_prompt_args.py` file entirely
- [ ] 1.3 Update imports in `guide_prompt.py` to remove argument class dependency
- [ ] 1.4 Clean up any unused prompt argument infrastructure

## 2. Implement MCP-Compatible Argument Handling
- [ ] 2.1 Replace prompt function signature with direct parameters (arg1-argF)
- [ ] 2.2 Implement argv-style parsing: ["guide", arg1, arg2, ...] stopping at None
- [ ] 2.3 Add parameter validation and help message for empty arguments
- [ ] 2.4 Update prompt decorator to use direct function parameters

## 3. MVP Content Access Implementation
- [ ] 3.1 Process first argument (arg1) as category/pattern for get_content
- [ ] 3.2 Handle empty arguments with usage help message
- [ ] 3.3 Reserve remaining arguments (arg2-argF) for future click integration
- [ ] 3.4 Maintain backward compatibility with existing content access patterns

## 4. Testing & Validation
- [ ] 4.1 Update existing prompt tests to use new argument format
- [ ] 4.2 Add tests for argv parsing logic (None handling, argument ordering)
- [ ] 4.3 Test various argument patterns: single, multiple, empty
- [ ] 4.4 Verify MCP client compatibility with space-separated arguments

## 5. Documentation Updates
- [ ] 5.1 Update prompt usage examples in docstrings
- [ ] 5.2 Document argv parsing behavior and limitations
- [ ] 5.3 Add examples for future click integration approach

## Implementation Notes

**Key Changes:**
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
