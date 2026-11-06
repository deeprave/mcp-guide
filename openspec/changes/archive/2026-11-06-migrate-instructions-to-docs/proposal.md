# Proposal

## Why

`INSTRUCTIONS.md` mixes reusable guidance, policy choices, and mcp-guide-specific steering in one repository file. Its content needs to be absorbed into the appropriate versioned template and policy mechanisms, while obsolete agent-tool prescriptions are retired.

## What Changes

- Replace the default `checks/instructions` template with unconditional, reusable AI best-practice guidance on code and pattern reuse.
- Move language-specific preferences into selected Python policies and language-specific concurrency policies.
- Add an MCP client/server state policy, offered by onboarding only when the project is detected as MCP development.
- Retire obsolete text-transformation-tool prohibitions from templates, onboarding, and active policies.
- Preserve mcp-guide-only template guidance in committed `.agents/steering` rather than shipping it to other projects.
- Track `.agents` by default, retaining OpenSpec skills while removing the superseded local review skill.
- Delete the superseded root `INSTRUCTIONS.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

This changes shipped onboarding and policy selection, but not the document-store or Guide-serving behaviour. It therefore continues to set `skip_specs: true`.

## Impact

- Removes `INSTRUCTIONS.md` and the default `checks/instructions` template.
- Adds reusable guidance and policies to the shipped template set.
- Updates onboarding and mcp-guide's active policy selections.
