## Why

Guide URL content is accessible through MCP resources, but it has not been
demonstrated that Codex will treat a Guide-served skill as instructions to
follow. Building package exchange, exports, and agent-specific integrations
before proving that interaction would add substantial complexity without
establishing the central value.

## What Changes

- Serve Guide skills as package-shaped resources rooted at `SKILL.md`, through a
  distinct Guide resource namespace and a standard `list_skills` tool. The catalogue
  contains enough metadata for an agent to explicitly select a package.
- Verify in a real Codex task that Codex retrieves that entrypoint through
  Guide and follows its instructions.
- Record the direct-serving result as the decision point for subsequent skill
  package, export, agent-mapping, and automatic-discovery work.
- Add an opt-in, negotiated MCP skills extension that lets a supporting client
  list the effective skills for its active Guide session and refresh that list
  when availability changes.
- Complete the accepted review remediations for literal package-member paths,
  structured skill errors, deferred list-change delivery, and URI routing.
- Port Guide's five workflow phases as flat, verb-named skill packages and keep
  workflow status focused solely on the configured workflow file.
- Add a `workflow-review` skill for independent, collated reviews and a
  `just-one` skill for recording the user's disposition of findings before any
  accepted work begins. Each reviewer records fresh findings in a
  machine-readable source-report directory; collation writes a separate
  canonical inventory for triage and hand-off without modifying the source
  reports.
- Let any skill entrypoint declare required MCP forms in frontmatter, so Guide
  requests missing input without hard-coding a package name or prescribing a
  client-specific question tool.

## Capabilities

### New Capabilities

- `guide-url-skills`: Serve a minimal, explicitly selected Guide skill.
- `mcp-skills-advertisement`: Experimentally advertise the Guide skill surface
  to MCP clients.

## Impact

- Resource discovery and rendering context.
- A real Codex integration exercise in addition to focused resource tests.
- No server-side script execution, automatic local package installation, or MCP v2
  engine migration. Scripts are retrievable package members that a client must inspect
  and explicitly choose to execute locally.
- A global, startup-scoped feature flag gates the complete protocol extension:
  its capability advertisement, `skills/list` method, and list-change
  notifications.
