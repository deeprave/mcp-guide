# Tasks

## 1. Formatters

- [x] 1.1 Change `RedactedFormatter` to `%(asctime)s [%(process)s]%(name)s - %(levelname)s - %(message)s`, and add or update the focused unit test in `tests/unit/test_mcp_core/test_mcp_log.py` for the formatted layout
- [x] 1.2 Add an integer `pid` field to `StructuredJSONFormatter` after `function`, and add a focused unit test for it
- [x] 1.3 Preserve the id through the redaction function in both formats, and add a focused unit test with an installed redaction function

## 2. Paths and processes

- [x] 2.1 Preserve the creating process's id for records replayed from the startup buffer and in the uvicorn log configuration, with focused unit tests for both paths
- [x] 2.2 Preserve each writing process's own id when two processes share a file handler, with a focused subprocess test

## 3. Documentation

- [x] 3.1 Add one or two sentences to the logging section of `docs/user/installation.md` saying each line (and JSON entry) carries the writing process's id
