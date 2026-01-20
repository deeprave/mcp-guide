# Change: Add OpenSpec Integration Support

## Why
Enable MCP-Guide to integrate with OpenSpec CLI for spec-driven development workflows. This provides a guided interface to OpenSpec commands through the MCP protocol, making OpenSpec workflows more accessible while delegating all OpenSpec logic to the official CLI.

## What Changes
- Add conditional OpenSpec detection via feature flag
- Implement guide command templates that invoke OpenSpec CLI through the agent
- Handle client-server filesystem separation for OpenSpec file access
- Integrate OpenSpec project state into template context hierarchy
- Provide guided workflows for common OpenSpec operations
- Format OpenSpec command responses (JSON) into user-friendly markdown

## Impact
- Affected specs: mcp-server, template-context
- Affected code: Template system, command infrastructure, client context tasks
- **BREAKING**: None - feature is conditional and additive
- Dependencies: OpenSpec CLI must be installed on client system
