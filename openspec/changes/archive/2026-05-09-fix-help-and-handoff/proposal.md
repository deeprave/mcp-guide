# Change: fix-help-and-handoff

## Why

The current `:help` display and `:handoff` command expose two related gaps in the
template system.

First, template authors can currently use the `resource` lambda to render content
references as either `guide://` URIs or `get_content(...)` tool calls, but there
is no equivalent helper for commands. That forces command references in templates
to be handwritten, which makes them inconsistent and limits templates like
`:help` from adapting command formatting cleanly across agents.

Second, the current `:handoff` command is too rigid. It always describes a
generic save-context flow and cannot explicitly tell the agent whether it should
read an existing handoff file or write a new one to a specific path. That makes
it less useful as a reusable command for structured context transfer.

## What Changes

- Rename the existing resource-formatting feature flag to `format-resource`,
  give it an explicit constant (`FLAG_RESOURCE`), and register it with the
  standard boolean validation/normalisation path
- Add a new `command` template helper family that can render command references
  in either URI form or tool-oriented form, depending on a new
  `format-command` feature flag (`FLAG_COMMAND`)
- Add a simple `{{prompt}}` template variable that exposes the effective prompt
  name for compatibility cases where the prompt name itself must be shown
- Update the `:help` template and other applicable command templates to use the
  shared command/resource helpers rather than hardcoded inline command or
  resource formatting
- Update the `:handoff` command template to accept a file path argument plus
  mutually exclusive `--read` and `--write` flags with explicit validation rules
- Allow the guide prompt name itself to be overridden by environment variable
  so prompt collisions can be avoided in clients that reserve `guide`
- Standardize static documentation on `guide://` URI syntax as the canonical
  form, with prompt-style syntax described only as an optional note or reminder

## Impact

- Affected specs:
  - `template-support`
  - `help-template-system`
- Likely affected implementation:
  - `src/mcp_guide/render/functions.py`
  - `src/mcp_guide/render/renderer.py`
  - `src/mcp_guide/feature_flags/constants.py`
  - `src/mcp_guide/feature_flags/validators.py`
  - prompt registration / prompt decorator code
  - `src/mcp_guide/templates/_commands/help.mustache`
  - `src/mcp_guide/templates/_commands/handoff.mustache`
  - other templates that currently hardcode command or resource references
  - `docs/user/feature-flags.md`
  - static command-oriented documentation that currently hardcodes prompt usage
- No new external dependencies expected
