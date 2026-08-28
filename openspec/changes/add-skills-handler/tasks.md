## 1. Package model and sequencing

- [ ] 1.1 Define the canonical skill package layout, supported Guide URL types, naming, and collision behaviour
- [ ] 1.2 Define skill catalog metadata, project-aware rendering boundaries, and package-member URI layout
- [ ] 1.3 Confirm the MCP v2 direct-serving bridge after `upgrade-mcp-version`; do not add v2 engine migration work here

## 2. Skill serving and exchange

- [ ] 2.1 Serve the skill catalog and package members, including `SKILL.md`, references, scripts, and assets
- [ ] 2.2 Add import and agent-native filesystem export adapters with agent-specific destination mappings
- [ ] 2.3 Report unsupported packages, URLs, agents, and collisions without creating partial files

## 3. Verification

- [ ] 3.1 Add package-layout, catalog, member retrieval, and invalid-input tests without coupling tests to rendered templates
- [ ] 3.2 Add import/export and output-path tests for supported agents
- [ ] 3.3 Document virtual skill serving, agent script execution, and supported export behaviour
