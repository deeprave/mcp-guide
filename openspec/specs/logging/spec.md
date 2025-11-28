# logging Specification

## Purpose
TBD - created by archiving change logging-implementation. Update Purpose after archive.
## Requirements
### Requirement: TRACE Level Support
The system SHALL provide a TRACE logging level (value 5) below DEBUG (value 10) for detailed execution tracing.

#### Scenario: TRACE level registration
- **WHEN** the logging module is imported
- **THEN** TRACE level is registered with the logging system
- **AND** `logging.getLevelName(5)` returns "TRACE"

#### Scenario: Logger trace method
- **WHEN** a logger is obtained via `get_logger()`
- **THEN** the logger has a `trace()` method
- **AND** calling `logger.trace("message")` logs at TRACE level

#### Scenario: TRACE level filtering
- **WHEN** log level is set to INFO or higher
- **THEN** TRACE messages are filtered out
- **AND** do not appear in output

### Requirement: File Logging with Rotation
The system SHALL support file logging with automatic rotation support on Unix/Linux systems.

#### Scenario: File handler creation
- **WHEN** `add_file_handler()` is called with a file path
- **THEN** a file handler is created and added to the root logger
- **AND** the file is created if it doesn't exist

#### Scenario: WatchedFileHandler on Unix
- **WHEN** running on Unix/Linux (platform != 'win32')
- **THEN** `WatchedFileHandler` is used for log rotation support
- **AND** external log rotation tools can safely rotate the file

#### Scenario: FileHandler on Windows
- **WHEN** running on Windows (platform == 'win32')
- **THEN** standard `FileHandler` is used
- **AND** logs are written to the specified file

#### Scenario: Log file append mode
- **WHEN** the log file already exists
- **THEN** new logs are appended to the existing file
- **AND** previous log entries are preserved

### Requirement: JSON Structured Logging
The system SHALL support JSON-formatted structured logging for machine parsing.

#### Scenario: JSON formatter creation
- **WHEN** `add_file_handler()` is called with `json_format=True`
- **THEN** logs are formatted as JSON objects
- **AND** each log entry includes timestamp, level, logger, message, module, and function fields

#### Scenario: Text formatter creation
- **WHEN** `add_file_handler()` is called with `json_format=False`
- **THEN** logs are formatted as human-readable text
- **AND** format is "YYYY-MM-DD HH:MM:SS - logger - LEVEL - message"

### Requirement: PII Redaction Stub
The system SHALL provide a redaction function stub for future PII filtering integration.

#### Scenario: Redaction function availability
- **WHEN** `get_redaction_function()` is called
- **THEN** a callable function is returned
- **AND** the function accepts a string and returns a string

#### Scenario: Pass-through behavior
- **WHEN** the redaction function is called with a message
- **THEN** the message is returned unchanged (pass-through)
- **AND** no redaction is performed in the current implementation

### Requirement: FastMCP Integration
The system SHALL integrate with FastMCP's logging system when available.

#### Scenario: FastMCP logger detection
- **WHEN** `get_logger()` is called and FastMCP is available
- **THEN** FastMCP's `get_logger()` is used
- **AND** the returned logger has TRACE support

#### Scenario: Fallback to standard logging
- **WHEN** `get_logger()` is called and FastMCP is not available
- **THEN** standard `logging.getLogger()` is used
- **AND** the returned logger still has TRACE support

#### Scenario: Context trace method
- **WHEN** FastMCP Context class is available
- **THEN** a `trace()` method is added to Context
- **AND** calling `await ctx.trace("message")` logs with "[TRACE]" prefix at debug level

### Requirement: Logger Hierarchy Separation
The system SHALL prevent log duplication between application and framework loggers.

#### Scenario: Application logger configuration
- **WHEN** `configure_logger_hierarchy()` is called with an app name
- **THEN** loggers matching `<app_name>.*` have `propagate = False`
- **AND** loggers matching `fastmcp.<app_name>.*` have `propagate = False`

#### Scenario: No log duplication
- **WHEN** an application logger emits a message
- **THEN** the message appears exactly once in the output
- **AND** is not duplicated by parent loggers

### Requirement: Message Sanitization
The system SHALL sanitize log messages to prevent log injection attacks.

#### Scenario: Newline sanitization
- **WHEN** a log message contains newline characters
- **THEN** `\n` is replaced with `\\n` in the output
- **AND** log entries remain on single lines

#### Scenario: Carriage return sanitization
- **WHEN** a log message contains carriage return characters
- **THEN** `\r` is replaced with `\\r` in the output
- **AND** log entries are not corrupted

### Requirement: Environment Variable Configuration
The system SHALL support configuration via environment variables for CLI usage.

#### Scenario: Log level configuration
- **WHEN** `MG_LOG_LEVEL` environment variable is set
- **THEN** the logging system uses that level
- **AND** valid values are TRACE, DEBUG, INFO, WARN, ERROR

#### Scenario: Log file configuration
- **WHEN** `MG_LOG_FILE` environment variable is set
- **THEN** logs are written to the specified file path
- **AND** if not set, no file logging occurs

#### Scenario: JSON format configuration
- **WHEN** `MG_LOG_JSON` environment variable is set to "true", "1", or "yes"
- **THEN** JSON formatting is enabled
- **AND** logs are written as JSON objects

### Requirement: Logging Configuration API
The system SHALL provide a simple configuration API for programmatic setup.

#### Scenario: Basic configuration
- **WHEN** `configure()` is called with default parameters
- **THEN** TRACE level is initialized
- **AND** Context.trace() is added if FastMCP is available

#### Scenario: File logging configuration
- **WHEN** `configure()` is called with `file_path` parameter
- **THEN** a file handler is added with the specified path
- **AND** the handler uses the specified level and format

#### Scenario: Logger hierarchy configuration
- **WHEN** `configure()` is called with `app_name` parameter
- **THEN** logger hierarchy is configured for that application
- **AND** log duplication is prevented

### Requirement: Reusable Module Design
The system SHALL be implemented as a reusable module independent of mcp-guide specifics.

#### Scenario: Module independence
- **WHEN** the mcp_core.mcp_log module is imported
- **THEN** it has no dependencies on mcp_guide
- **AND** can be used in other applications

#### Scenario: Optional FastMCP dependency
- **WHEN** FastMCP is not installed
- **THEN** the module still functions correctly
- **AND** falls back to standard logging gracefully

