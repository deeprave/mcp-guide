## 1. Capture completed inputs from the exploration
- [x] 1.1 Confirm that first-pass optimized support should be scoped narrowly
- [x] 1.2 Confirm that fallback explanation wording should be standardized
- [x] 1.3 Confirm that Codex local / in-session remains in scope for first-pass optimized support
- [x] 1.4 Confirm that Cursor / cursor-agent is fallback-only for now

## 2. Preserve and extend the template agent context
- [x] 2.1 Confirm that existing `agent.class` and `agent.prefix` context is already exposed
- [x] 2.1 Extend agent context to expose `agent.has_handoff`
- [x] 2.2 Default `agent.has_handoff` to `false`
- [x] 2.3 Expose `agent.is_<normalized-name>` boolean flags for the examined client set
- [x] 2.4 Keep existing `agent.class` and `agent.prefix` behavior intact after the new flags are added

## 3. Normalize the examined client set
- [x] 3.1 Review and update agent normalization patterns for the explored client set
- [x] 3.2 Preserve q-dev lineage handling for Amazon Q Developer, Kiro, and Kiro CLI
- [x] 3.3 Ensure normalized-name flags are derived from the canonical normalized name rather than raw client strings
- [x] 3.4 Verify that unknown agents still render safely with `agent.has_handoff=false`

## 4. Implement first-pass handoff support in templates
- [x] 4.1 Update `_commands/document/add.mustache` to branch on `agent.has_handoff`
- [x] 4.2 Update `_commands/document/add-url.mustache` to branch on `agent.has_handoff`
- [x] 4.3 Update `_commands/export/add.mustache` to branch on `agent.has_handoff`
- [x] 4.4 Review `_commands/document/update.mustache` and keep it inline unless a concrete handoff benefit is justified during implementation
- [x] 4.5 Add standardized fallback wording to the inline path
- [x] 4.6 Keep client-specific wording light and optional inside the shared handoff branch

## 5. Validate the first-pass client set under the new templates
- [x] 5.1 Validate q-dev lineage behavior and record that fallback currently works
- [x] 5.2 Validate Claude Code behavior for the handoff branch
- [x] 5.3 Validate Codex local / in-session behavior for the handoff branch
- [x] 5.4 Validate that non-handoff clients fall back cleanly
- [x] 5.5 Validate that Cursor remains fallback-only under the new templates
- [x] 5.6 Validate that export handoff still writes the requested file and reports success/failure correctly

## 6. Capture follow-on scope explicitly
- [x] 6.1 Record that broader client validation continues separately from this change
- [x] 6.2 Leave non-validated clients on the inline fallback path
- [x] 6.3 Note any wording or behavior differences that justify a follow-up tuning change

## Validation notes

- Codex local / in-session is validated for end-to-end handoff, including `send_file_content`.
- Claude Code is validated for separate execution / background-agent behavior, including export.
- q-dev lineage remains enabled for handoff attempts. Current validation shows reliable fallback behavior, while background execution may improve as delegate support evolves.
- Cursor remains fallback-only.

## Immediate implementation order

1. Finish agent normalization and context flags:
   - 3.1
   - 3.2
   - 3.3
   - 2.1
   - 2.2
   - 2.3
   - 2.4
2. Update the long-running templates:
   - 4.1
   - 4.2
   - 4.3
   - 4.5
   - 4.6
3. Review the non-long-running document mutation template:
   - 4.4
4. Run focused validation:
   - 5.1
   - 5.2
   - 5.3
   - 5.4
   - 5.5
   - 5.6
5. Record what remains for later:
   - 6.1
   - 6.2
   - 6.3

## Already satisfied before implementation starts

- 1.1 through 1.4 are satisfied by the completed exploration
- 2.1 is satisfied by the current codebase: `agent.class` and `agent.prefix` are already exposed in template context
