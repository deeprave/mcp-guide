## UK/AU Spelling

You are to use UK/AU spelling in all written text, documentation, symbols, variable, function, commentsm file and directory names.
But there do exist rare exceptions widely accepted industry spellings such as "license", "artifact" and software colloquialisms.

## Guide MCP Response Handling

- Always respect instructions and special_agent_instructions embedded in an MCP response,
- When an MCP Guide response instructs you to present information to the user without interpretation, reproduce the returned information exactly and verbatim (only markdown formatting allowed) - do not paraphrase, abbreviate, interpret, summarise information that MCP Guide instructs you to present verbatim.
- Follow every `additional_agent_instructions` value returned by MCP Guide.
- If told to `set_project`, provide it with the project root directly and immediately.

These rules are critical for MCP operations to work correctly.

## Git Commit Safety

- NEVER EVER use `--no-verify` under any circumstances unless explicitly requested by the user.
- Do not bypass commit checks.
- NEVER use `--no-gpg-sign`; this is forbidden with no exceptions.
- Do not bypass commit signing.

## Pytest Execution

- Run every pytest invocation in a foreground terminal, including direct `pytest` commands and indirect invocations through pre-commit or `git commit` hooks.
- Do not run pytest in a background or short-lived execution context; wait for its complete result before proceeding.

## Workflow Handover

- After each significant milestone, update `.todo/context.json` with the current handover context so work can be resumed reliably by this or another agent.
- This is for AI consumption so should be concise but sufficient.
- Together with .guide.yaml this context keeps track of:
  - current workflow phase
  - issue status
  - recently completed work
  - remaining work to be done
  - any blockers
  - immediate expected next action.
- This is not a historical document; remove any item that is no longer relevant whenever the file is updated.
