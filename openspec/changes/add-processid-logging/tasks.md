# Tasks

## 1. Formatters

- [ ] 1.1 Change `RedactedFormatter` to `%(asctime)s [%(process)s]%(name)s - %(levelname)s - %(message)s`; verify with a unit test in `tests/test_mcp_core/test_mcp_log.py` that a formatted record's line is `<timestamp> [<id>]<logger> - <LEVEL> - <message>` and that existing assertions are updated to the new layout
- [ ] 1.2 Add an integer `pid` field to `StructuredJSONFormatter` after `function`; verify with a unit test that the field equals the record's process id and the existing fields are unchanged
- [ ] 1.3 Verify the id survives the redaction function in both formats with a unit test that installs a redaction function

## 2. Paths and processes

- [ ] 2.1 Verify records replayed from the startup buffer, and the uvicorn log configuration, carry the creating process's id; verify with unit tests for the buffered replay and for the formatter named by `get_uvicorn_log_config()`
- [ ] 2.2 Verify that two processes writing to one file produce lines with their own, differing ids; verify with a test that launches two short `sys.executable` subprocesses writing through the module's file handler to a `tmp_path` file and asserts each line's id matches the process that wrote it

## 3. Documentation

- [ ] 3.1 Add one or two sentences to the logging section of `docs/user/installation.md` saying each line (and JSON entry) carries the writing process's id; verify the strict MkDocs build passes
- [ ] 3.2 Run the full pytest suite (foreground), Ruff and Ty; verify all pass
