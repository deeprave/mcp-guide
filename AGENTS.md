## MCP Response Handling

- Always respect instructions embedded in a response.
- Always respect `additional_agent_instructions` embedded in a response.
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
