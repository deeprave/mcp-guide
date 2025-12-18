# Change: Add @guide Prompt for Direct Content Access

## Why
Currently users must request documents from the guide MCP server via agent requests, which can lead to misunderstandings and the agent spending time trying to "fix" issues by second-guessing user intent. This creates inefficiency and takes the agent outside its intended scope.

## What Changes
- Add a `@guide` prompt that accepts variable arguments using MCP-compatible approach
- Remove complex `GuidePromptArguments` class due to MCP prompt argument limitations
- Implement direct function parameters: `arg1` through `argF` (15 total optional string parameters)
- Parse arguments into argv-style list: `["guide", arg1, arg2, ...]` stopping at first None
- MVP implementation processes first argument as category/pattern for `get_content`
- Reserve remaining arguments for future click-based command-line processing

## Technical Constraints
- MCP prompts don't support `*args` or `**kwargs` (FastMCP limitation)
- MCP clients parse space-separated arguments into individual parameters
- Single string parameter approach fails due to argument splitting behavior
- Fixed parameter count is the only viable solution for variable arguments

## Impact
- Affected specs: mcp-server, prompt-infrastructure
- Affected code: server.py, guide_prompt.py, guide_prompt_args.py (removal)
- **BREAKING**: Remove `GuidePromptArguments` class (currently unused externally)
- Users get direct access to guide content without agent interpretation layer
- Future extensibility via click command-line parsing framework
