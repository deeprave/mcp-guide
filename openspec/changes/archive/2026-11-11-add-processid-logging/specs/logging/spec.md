# Spec Delta

## MODIFIED Requirements

### Requirement: JSON Structured Logging
The system SHALL support JSON-formatted structured logging for machine parsing.

#### Scenario: JSON formatter creation
- **WHEN** `add_file_handler()` is called with `json_format=True`
- **THEN** logs are formatted as JSON objects
- **AND** each log entry includes timestamp, level, logger, message, module, function, and pid fields

#### Scenario: Text formatter creation
- **WHEN** `add_file_handler()` is called with `json_format=False`
- **THEN** logs are formatted as human-readable text
- **AND** format is "YYYY-MM-DD HH:MM:SS [<pid>]logger - LEVEL - message"

## ADDED Requirements

### Requirement: Process identifier in log entries
The system SHALL identify the process that wrote every log entry, in both text and JSON
output, using the operating-system process id read when the entry was created. It SHALL NOT
require emitting code to supply the identifier.

#### Scenario: Text entry carries the process id
- **WHEN** a record is formatted with the text formatter
- **THEN** the line contains `[<id>]` after the timestamp and a single space, directly followed by the logger name
- **AND** `<id>` is the id of the process that created the record

#### Scenario: JSON entry carries the process id
- **WHEN** a record is formatted with the JSON formatter
- **THEN** the entry contains a `pid` field holding that process id as an integer
- **AND** all other fields keep their existing names and values

#### Scenario: Entries from separate processes sharing one file
- **WHEN** two Guide processes write to the same log file
- **THEN** each line carries the id of the process that wrote it
- **AND** the ids on the two processes' lines differ

#### Scenario: Identifier is available to every output path
- **WHEN** a record is emitted through the console handler, the file handler, or the uvicorn log
  configuration
- **THEN** its formatted output carries the process id

#### Scenario: Records created before logging is configured
- **WHEN** a record is created before handlers exist and is replayed after configuration
- **THEN** its output carries the id of the process that created it
