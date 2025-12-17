# Change: Add @guide Prompt for Direct Content Access

## Why
Currently users must request documents from the guide MCP server via agent requests, which can lead to misunderstandings and the agent spending time trying to "fix" issues by second-guessing user intent. This creates inefficiency and takes the agent outside its intended scope.

## What Changes
- Add a `@guide` prompt that accepts zero, one, or multiple parameters
- MVP implementation executes `get_content` based on category and/or patterns provided by user
- Create `PromptArguments` protocol similar to `ToolArguments` for type safety
- Implement `GuidePromptArguments` class with `command: Optional[str]` and `arguments: List[str]`
- For MVP, pass `command` directly to existing `get_content` tool
- Reserve `arguments` for future enhancements

## Impact
- Affected specs: mcp-server, prompt-infrastructure, tool-infrastructure
- Affected code: server.py, new prompt infrastructure files
- **BREAKING**: None - this is additive functionality
- Users get direct access to guide content without agent interpretation layer
