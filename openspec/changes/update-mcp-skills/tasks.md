# Tasks

## 1. Standard skills transport

- [ ] 1.1 Replace the private negotiated skills extension with the SEP-2640 `io.modelcontextprotocol/skills` capability and standard `skills/list` and `skills/get` operations for modern clients, retiring the `mcp-skills` feature flag.
- [ ] 1.2 Serve effective Guide skill entrypoints and package members through stable `skill://` resource URIs, using dynamic resource declarations and existing shared rendering safeguards.
- [ ] 1.3 Add the capability-aware `skill` template section, retain Guide URI delivery for legacy or non-negotiating clients, and remove the private opaque-session request contract while retaining the post-binding refresh notification.

## 2. Binding-aware discovery

- [ ] 2.1 Refactor skill metadata discovery so it can build an unbound catalogue independently of project-specific requirement evaluation.
- [ ] 2.2 Add and enforce `allow-unbound` frontmatter so only explicitly opted-in packages are available before binding and project-dependent packages appear after a bound refresh.
- [ ] 2.3 Revise workflow-status and Git packages for complete unbound rendering, isolating selected project-policy instructions behind the bound-project context, and update the affected extension coverage.
