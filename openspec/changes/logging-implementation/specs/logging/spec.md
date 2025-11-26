# Logging Capability

## ADDED Requirements

### Requirement: TRACE Logging Level
The system SHALL provide a TRACE logging level below DEBUG for detailed debugging.

#### Scenario: TRACE level registration
- **WHEN** the logging module is initialized
- **THEN** TRACE level (value=5) is registered with Python logging
- **AND** logger.trace() method is available on all logger instances

#### Scenario: TRACE level usage
- **WHEN** logger.trace("message") is called
- **THEN** the message is logged at TRACE level
- **AND** the message appears in configured outputs if level is TRACE or lower

### Requirement: File Logging with Rotation Support
The system SHALL support file logging with automatic file recreation after external rotation.

#### Scenario: File logging on Unix/Linux
- **WHEN** file logging is configured on Unix/Linux
- **THEN** WatchedFileHandler is used
- **AND** file is automatically reopened if deleted or rotated externally

#### Scenario: File logging on Windows
- **WHEN** file logging is configured on Windows
- **THEN** FileHandler is used
- **AND** file is created if it doesn't exist

### Requirement: JSON Structured Logging
The system SHALL support JSON-formatted log output for structured logging.

#### Scenario: JSON formatter
- **WHEN** JSON formatting is enabled for file logging
- **THEN** log entries are written as JSON objects
- **AND** each entry includes timestamp, level, logger, message, module, function
- **AND** exception information is included if present

### Requirement: Logger Hierarchy Separation
The system SHALL prevent log duplication between application and FastMCP loggers.

#### Scenario: Application logger configuration
- **WHEN** application loggers are configured
- **THEN** both direct (mcp_guide.*) and FastMCP-prefixed (fastmcp.mcp_guide.*) patterns are handled
- **AND** propagate is set to False on application loggers
- **AND** logs appear once in configured outputs

### Requirement: PII Redaction Integration
The system SHALL provide a redaction function API for future PII filtering.

#### Scenario: Redaction stub
- **WHEN** get_redaction_function() is called
- **THEN** a callable function is returned
- **AND** the function accepts a string message
- **AND** the function returns the message unchanged (pass-through)

#### Scenario: Formatter integration
- **WHEN** formatters are created
- **THEN** they call get_redaction_function()
- **AND** they apply the redaction function to log messages
- **AND** no errors occur if redaction is not configured

### Requirement: Context TRACE Logging
The system SHALL provide Context.trace() for client-visible TRACE logging.

#### Scenario: Context.trace() method
- **WHEN** Context.trace() is called in a tool
- **THEN** the message is sent to the MCP client at debug level
- **AND** the message is prefixed with "[TRACE]" to distinguish from regular debug
- **AND** the message is sanitized to prevent log injection

### Requirement: Configuration via Environment Variables
The system SHALL support logging configuration via environment variables.

#### Scenario: Log level configuration
- **WHEN** MG_LOG_LEVEL environment variable is set
- **THEN** the logging level is configured accordingly
- **AND** TRACE, DEBUG, INFO, WARN, ERROR, OFF levels are supported

#### Scenario: File logging configuration
- **WHEN** MG_LOG_FILE environment variable is set
- **THEN** file logging is enabled to the specified path
- **AND** the file is created if it doesn't exist

#### Scenario: JSON format configuration
- **WHEN** MG_LOG_JSON environment variable is set to true
- **THEN** JSON formatting is enabled for file logging
- **AND** console logging remains in text format

### Requirement: Log Message Sanitization
The system SHALL sanitize log messages to prevent log injection attacks.

#### Scenario: Newline sanitization
- **WHEN** a log message contains newline characters
- **THEN** newlines are escaped as "\\n"
- **AND** carriage returns are escaped as "\\r"
- **AND** the sanitized message is logged
