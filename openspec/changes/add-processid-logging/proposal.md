# Proposal

## Why

Several Guide servers often write to one log file at the same time. A single MCP client can spawn
more than one (Codex starts a server per thread, and its desktop and CLI sessions share the same
configured `--log-file`), and a user may point several agents at one file. Log lines carry no
process identity, so a line cannot be attributed to the server that wrote it. This blocked a real
diagnosis during the elicitation work: `/tmp/codex-guide.log` held interleaved output from the CLI
and desktop sessions, and it was impossible to tell whose requests produced which outcomes, even
though only one of the servers had a given option set.

The process id is already known to Python's logging machinery (`LogRecord.process`), but neither
formatter prints it.

## What Changes

- The text formatter prints the writing process's id on every entry, in brackets directly before the
  logger name: `YYYY-MM-DD HH:MM:SS [12345]mcp_guide.x - DEBUG - message`.
- The JSON formatter includes the writing process's id as a field on every entry.
- The process id is read from the standard `LogRecord.process` attribute, so no new state is
  recorded on the record and no emitter changes are needed. Console, file and uvicorn output all
  use the same formatters and therefore gain it.
- **BREAKING (log format):** the text line gains the `[pid]` field and the separator between the
  timestamp and the logger name changes from ` - ` to a single space, so tools that split lines on
  ` - ` or parse them positionally need updating. The JSON fields are unchanged apart from the
  new `pid`, and keep their order.
- Document the new field briefly in the logging section of the installation guide.

Out of scope: session, request or correlation identifiers, log levels, rotation, and any change
to what is logged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `logging`: add a requirement that every text and JSON log entry identifies the writing process,
  and update the "JSON Structured Logging" requirement whose text and JSON field lists change.

## Impact

- `src/mcp_guide/core/mcp_log.py` (`RedactedFormatter`, `StructuredJSONFormatter`).
- `tests/test_mcp_core/test_mcp_log.py` and a test for output from separate processes.
- `docs/user/installation.md` (logging section).
- Anything that parses Guide's text log lines by position. None exists in this repository.
