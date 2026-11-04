# Design

## Context

Guide's two formatters live in `src/mcp_guide/core/mcp_log.py`. `RedactedFormatter` builds the
text line from `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` and appends
` - extra: {...}`. `StructuredJSONFormatter` builds a dict of fixed fields plus the record's extras.
Both deliberately exclude standard `LogRecord` attributes, including `process`, from the "extra"
data. `create_formatter()` chooses between them for the console and file handlers, and
`get_uvicorn_log_config()` names the same classes for uvicorn. Records emitted before
configuration are buffered by `StartupBufferingHandler` and replayed to file handlers.

See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Every entry, in every output path and both formats, identifies its writing process.
- No change to any emitter.

**Non-Goals:**
- Session, request or correlation identifiers.
- Per-instance or per-client identity beyond the process.
- Changes to levels, rotation, redaction or what is logged.

## Decisions

1. **Read `LogRecord.process`; record nothing new.** The logging module sets `record.process`
   to `os.getpid()` when it creates the record, which is exactly the "who wrote this" we need,
   it is correct across forks and multiprocessing, and it is already excluded from the extras
   so it cannot be double-printed. Alternatives rejected: a logging `Filter` or adapter that
   adds an attribute (extra moving part, would have to be installed on every logger or handler),
   and stamping the id into each message (touches every call site).
2. **Materialise it in the formatters.** Both formatters already own the line layout, so the
   change is local to them and reaches console, file and uvicorn output automatically.
3. **Text layout: `<timestamp> [<id>]<logger> - <LEVEL> - <message>`.** For example
   `2026-11-03 17:24:21 [12345]mcp_guide.x - DEBUG - message`. The id is compact, bracketed so it
   reads as a tag, and grep-friendly (`grep '\[39538\]'`); attaching it to the logger name keeps the
   prefix short, and the level and message tail is untouched. It replaces the ` - ` between timestamp
   and logger with a space, which is part of the format change. Alternatives: a longer labelled token
   such as `pid=12345 - ` (rejected as too verbose), or a bare number after the timestamp (ambiguous).
   Rich's markup is off by default and Guide does not enable it on the console handler, so square
   brackets are shown literally there.
4. **JSON field name `pid`, integer.** Short, conventional, and does not collide with the existing
   `timestamp`, `level`, `logger`, `message`, `module`, `function` keys. Added after `function`
   so existing fields keep their order.
5. **Console handler.** The Rich console handler renders its own columns and prints the formatted
   text as the message, so the id appears in the message text there. That is acceptable: console
   output is for a human watching one process.

## Risks / Trade-offs

- [Parsers of the text log break] -> Documented as a format change in the proposal, including the
  changed separator; the repository has none; the JSON format only gains a field.
- [Longer lines] -> A fixed few characters per entry; accepted.
- [Rich console shows the id inside the message] -> Accepted, see decision 5.
- [Redaction] -> The redaction function runs over the formatted string; a numeric id is not
  matched by it, and the test asserts the id survives redaction.

## Open Questions

- None that affect scope or tasks. The text placement (decision 3) and the JSON key (decision 4)
  are assumptions that can be changed before implementation without altering the tasks.
