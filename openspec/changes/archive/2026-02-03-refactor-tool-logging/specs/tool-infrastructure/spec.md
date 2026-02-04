# tool-infrastructure Specification Delta

## ADDED Requirements

### Requirement: Tool Result Helper Function
The system SHALL provide a `_tool_result()` helper function for consistent result processing and logging.

#### Scenario: Result processing and logging
- **WHEN** tool completes with Result object
- **THEN** tool calls `_tool_result(tool_name, result)`
- **AND** helper processes result through TaskManager if available
- **AND** helper logs result at TRACE level with result.to_json()
- **AND** helper returns result.to_json_str() for FastMCP

#### Scenario: TaskManager integration
- **WHEN** TaskManager is available
- **THEN** `_tool_result()` calls `task_manager.process_result(result)`
- **AND** processing happens before JSON conversion
- **AND** processing happens before logging

#### Scenario: TaskManager unavailable
- **WHEN** TaskManager is not available
- **THEN** `_tool_result()` skips TaskManager processing
- **AND** continues with logging and JSON conversion
- **AND** no errors are raised

#### Scenario: Consistent tool pattern
- **WHEN** any tool returns a result
- **THEN** tool uses `return _tool_result("tool_name", result)`
- **AND** tool_name matches the function name (without prefix)
- **AND** pattern is consistent across all tools

## MODIFIED Requirements

### Requirement: Automatic Tool Logging
The system SHALL log tool results through `_tool_result()` helper, not through decorator.

#### Scenario: Tool result logging
- **WHEN** tool calls `_tool_result()`
- **THEN** TRACE level log entry created with tool name and result.to_json()
- **AND** logging happens before JSON string conversion
- **AND** logging has access to Result object structure

#### Scenario: Tool invocation logging (unchanged)
- **WHEN** tool is called
- **THEN** DEBUG level log entry created with "Invoking async tool: {name}"
- **AND** log entry created before tool executes

#### Scenario: Tool completion logging (unchanged)
- **WHEN** tool completes successfully
- **THEN** DEBUG level log entry created with "Tool {name} completed successfully"

#### Scenario: Tool failure logging (unchanged)
- **WHEN** tool raises exception
- **THEN** ERROR level log entry created with "Tool {name} failed: {error}"
- **AND** exception is re-raised after logging

### Requirement: Tool Integration Pattern
The system SHALL call `on_tool()` at tool start and use `_tool_result()` for result processing.

#### Scenario: Tool start hook
- **WHEN** tool is invoked
- **THEN** decorator calls `task_manager.on_tool()` immediately
- **AND** call happens before tool logic executes
- **AND** call is independent of result processing

#### Scenario: Tool result processing
- **WHEN** tool completes with Result object
- **THEN** tool calls `_tool_result(tool_name, result)`
- **AND** `_tool_result()` handles TaskManager processing
- **AND** `_tool_result()` handles logging
- **AND** `_tool_result()` returns JSON string for FastMCP

#### Scenario: Decorator simplification
- **WHEN** decorator wraps tool function
- **THEN** decorator calls `on_tool()` at start
- **AND** decorator returns tool result directly
- **AND** decorator does not process Result objects
- **AND** decorator does not log results

## REMOVED Requirements

None. This change refactors existing functionality without removing requirements.
