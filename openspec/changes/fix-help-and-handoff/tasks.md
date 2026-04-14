## 1. Feature flag registration

- [x] 1.1 Rename the existing resource-formatting flag from `content-accessor` to `format-resource`, expose it as `FLAG_RESOURCE`, and register it with the standard boolean validator and normaliser path
- [x] 1.2 Add a new `format-command` feature flag constant exposed as `FLAG_COMMAND`
- [x] 1.3 Register `format-command` with the standard boolean validator and normaliser path
- [x] 1.4 Reverse the accessor semantics so `false` or unset means URI form and `true` means tool-oriented rendering
- [x] 1.5 Update user-facing feature flag documentation to describe both formatting flags and their URI-first defaults

## 2. Command helper implementation

- [x] 2.1 Extend template helper support in `src/mcp_guide/render/functions.py` to add `command`, `command-args`, `command-flags`, and `command-alias`
- [x] 2.2 Implement composition logic so adjacent helper sections contribute to one command reference
- [x] 2.3 Implement URI rendering for command references in `guide://_{command}` form with path args and query flags
- [x] 2.4 Implement tool-oriented rendering for command references when `format-command` is `true`
- [x] 2.5 Make URI rendering the universal default when `format-command` is unset
- [x] 2.6 Register the new helper family in the render context

## 3. Prompt name override

- [x] 3.1 Add support for `MCP_PROMPT_NAME` to override the default prompt command name
- [x] 3.2 Ensure prompt registration uses the overridden name when present
- [x] 3.3 Ensure prompt-style command rendering uses the overridden name when present
- [x] 3.4 Ensure `guide://` URI rendering remains unaffected by the prompt name override
- [x] 3.5 Expose the effective prompt name through `{{prompt}}` for compatibility cases

## 4. Help template update

- [x] 4.1 Update `src/mcp_guide/templates/_commands/help.mustache` to render command references through the shared command helper family
- [x] 4.2 Ensure aliases remain visible and formatted consistently with the chosen `format-command` mode
- [x] 4.3 Verify both general help listing and individual command help still render correctly
- [x] 4.4 Migrate other applicable templates away from hardcoded command/resource references to the shared helper family

## 5. Handoff command update

- [x] 5.1 Update `src/mcp_guide/templates/_commands/handoff.mustache` to require a path argument
- [x] 5.2 Add explicit `--read` and `--write` handling in the command template
- [x] 5.3 Add validation/error behavior for missing path, missing mode, and mutually exclusive mode flags
- [x] 5.4 Ensure the rendered instructions clearly distinguish read workflow from write workflow

## 6. Validation and tests

- [x] 6.1 Add or update tests for `format-resource` / `format-command` flag validation and normalisation
- [x] 6.2 Add or update tests for command helper rendering in both URI and tool-oriented modes
- [x] 6.3 Add or update tests for `MCP_PROMPT_NAME` prompt override behavior
- [x] 6.4 Add or update tests for `:handoff` validation and rendered mode-specific instructions
- [x] 6.5 Run `openspec validate fix-help-and-handoff --strict --no-interactive`
- [x] 6.6 Run the relevant focused test suite for the touched rendering/template code

## 7. Static documentation cleanup

- [x] 7.1 Review static documentation for hardcoded prompt-style guide command examples
- [x] 7.2 Standardize static docs on `guide://` as the canonical documented form
- [x] 7.3 Where helpful, add a short note that prompt-style invocation may also be available depending on client and prompt name
