# ADR-003: Result Pattern for Tool and Prompt Responses

**Date:** 2025-11-25
**Status:** Accepted
**Context:** Tool and Prompt Response Handling

## Problem

Current boolean return patterns (`True`/`False`) mask critical error information:
- Error messages may provide little diagnostic information
- Users receive no actionable feedback
- Agents receive no actionable feedback, and often pointlessly try many things as corrective actions.

## Decision

Implement a Kotlin-like Result pattern throughout the MCP server:

```python
"""Result pattern for rich error handling."""

import json
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """Result pattern for rich error handling.

    Generic result type that can hold any value type.
    Provides rich error information and agent guidance through instruction field.
    """

    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    exception: Optional[Exception] = field(default=None, repr=False, compare=False)
    message: Optional[str] = None
    instruction: Optional[str] = None
    error_data: Optional[dict[str, Any]] = None

    @classmethod
    def ok(cls, value: T, message: Optional[str] = None, instruction: Optional[str] = None) -> "Result[T]":
        """Create a successful result.

        Args:
            value: Result value (can be None)
            message: Optional message
            instruction: Optional instruction for agent

        Returns:
            Result with success=True
        """
        return cls(success=True, value=value, message=message, instruction=instruction)

    @classmethod
    def failure(
        cls,
        error: str,
        error_type: str = "unknown",
        exception: Optional[Exception] = None,
        message: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> "Result[T]":
        """Create a failure result with error information.

        Args:
            error: Error message
            error_type: Error classification
            exception: Original exception (optional)
            message: Optional message
            instruction: Optional instruction for agent

        Returns:
            Result with success=False
        """
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            exception=exception,
            message=message,
            instruction=instruction,
        )

    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return not self.success

    def to_json(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON format."""
        if self.success:
            result: dict[str, Any] = {"success": True}
            if self.value is not None:
                result["value"] = self.value
        else:
            result = {
                "success": False,
                "error": self.error,
                "error_type": self.error_type,
            }
            if self.error_data:
                result["error_data"] = self.error_data
            # Include exception details for debugging
            if self.exception:
                result["exception_type"] = type(self.exception).__name__
                result["exception_message"] = str(self.exception)

        if self.message:
            result["message"] = self.message
        if self.instruction:
            result["instruction"] = self.instruction

        return result

    def to_json_str(self) -> str:
        """Convert to JSON string for MCP tool responses."""
        return json.dumps(self.to_json())
```

## Benefits

- **Rich Error Information**: Specific error messages and types
- **Better Debugging**: Clear distinction between error types + original exception preservation
- **User Feedback**: Actionable error messages for users
- **Agent Guidance**: Instructions field controls agent behavior on responses
- **Consistent Pattern**: Uniform error handling across the system
- **Type Safety**: Generic type support for different return types
- **MCP Compatibility**: Direct JSON serialization for MCP tool responses
- **Exception Preservation**: Original exceptions stored for detailed debugging

## Field Usage

### Success Response Fields

- `success: bool = True` - Explicit success indicator (required)
- `value: Optional[T]` - Result data (optional - some operations just indicate success without returning data)
- `message: Optional[str]` - Information message for the user (can be set via `Result.ok(value, message=...)`)
- `instruction: Optional[str]` - Guidance for the agent on how to handle the response (can be set via `Result.ok(value, instruction=...)`)

### Failure Response Fields

- `success: bool = False` - Explicit failure indicator (required)
- `error: str` - What went wrong (required for failures)
- `error_type: str` - Classification of error (required for failures, defaults to "unknown")
- `exception: Optional[Exception]` - Original exception object for debugging (automatically serialized to `exception_type` and `exception_message` strings in JSON)
- `message: Optional[str]` - User-facing error explanation (can be set via `Result.failure(error, message=...)`)
- `instruction: Optional[str]` - How agent should handle the error (can be set via `Result.failure(error, instruction=...)`)
- `error_data: Optional[dict[str, Any]]` - Additional structured error data for programmatic handling

### Instruction Field Semantics

The `instruction` field provides guidance to AI agents on how to respond to the result:

**Error Handling Patterns:**
- `"Present this error to the user and take no further action."` - Prevents unwanted remediation attempts
- `"Suggest [specific remediation] before retrying."` - Guides agent toward solution
- `"Ask the user for clarification on [specific aspect]."` - Requests user input

**Mode Control Patterns:**
- `"Switch to PLANNING mode."` - Changes operational mode
- `"You are now in DISCUSSION mode."` - Sets context
- `"Return to CHECK mode."` - Transitions workflow state

**Operational Boundary Patterns:**
- `"Do NOT make any changes to the project."` - Prevents actions
- `"Require explicit user consent before proceeding."` - Enforces safety
- `"This operation requires user review and approval."` - Adds checkpoint

### JSON Serialization

The `to_json()` method handles serialization of all fields:

**Exception Handling:** The `exception` field stores the actual Exception object for debugging in Python code. When serializing to JSON via `to_json()`, it is automatically converted to JSON-safe format:
- `exception_type`: Exception class name (e.g., "FileNotFoundError")
- `exception_message`: String representation of the exception

**Error Data:** The `error_data` field provides structured error information for programmatic handling. Only included in JSON output when present.

**Value Serialization:** Only the `value: T` field requires T to be JSON-serializable. Acceptable types:
- Primitive types: `str`, `int`, `float`, `bool`, `None`
- Collections: `list`, `dict`, `tuple`
- Types with `.to_dict()` or `.to_json()` methods
- Pydantic models (auto-serializable)

## Implementation

1. Create `Result` class in `result.py`
2. All prompts and tools to return Result responses to the MCP by default
3. Update error handling to provide specific error information
4. Include original exceptions for debugging
5. Add MCP-compatible JSON serialization
6. Maintain backward compatibility where needed

## MCP Integration

The Result pattern integrates seamlessly with MCP tool responses.

## Implementation Strategy

- Phase 1: Implement Result class
- Phase 2: Update prompt methods
- Phase 3: Update tool methods
- Phase 4: Update other critical methods
- Phase 5: Update MCP tool responses to use rich error information

## Status

Accepted - to be implemented in mcp-guide v2 as part of mcp_core package.

## Amendment: Result Rendering Rule (2025-12-07)

**ABSOLUTE RULE:** Only MCP tools may render `Result` objects to JSON strings via `.to_json_str()`.

### Rationale

Internal functions that render Result to JSON create wasteful serialization/deserialization cycles:

```python
# ❌ WRONG - Internal function renders Result
async def internal_function() -> str:
    result = do_work()
    return Result.ok(result).to_json_str()  # Renders too early

# Caller must parse JSON we just created
result_str = await internal_function()
result = json.loads(result_str)  # Wasteful parsing
```

```python
# ✅ CORRECT - Internal function returns Result object
async def internal_function() -> Result[T]:
    result = do_work()
    return Result.ok(result)  # Returns Result object

# Caller uses Result directly
result = await internal_function()
if result.is_ok():
    value = result.value  # Direct access, no parsing
```

### Rule Enforcement

**Allowed:**
- MCP tools (functions decorated with `@tools.tool()`) may call `.to_json_str()` immediately before returning
- This is the ONLY place where Result rendering is permitted

**Prohibited:**
- Internal functions MUST NOT call `.to_json_str()`
- Helper functions MUST NOT call `.to_json_str()`
- Service functions MUST NOT call `.to_json_str()`
- Any function that is not an MCP tool MUST NOT call `.to_json_str()`

### Benefits

1. **Eliminates Waste:** No unnecessary JSON serialization/deserialization
2. **Type Safety:** Result objects provide compile-time type checking
3. **Cleaner Code:** Direct access to Result fields without parsing
4. **Better Testing:** Tests use Result objects directly, no `json.loads()` needed
5. **Clear Boundaries:** Rendering only happens at MCP boundary

### Validation

Periodically validate compliance:
```bash
# Should return ZERO matches (only tool functions allowed)
grep -rn "\.to_json_str()" src/mcp_guide/ --include="*.py" | grep -v "tools/tool_"
```

### Migration

When refactoring functions that violate this rule:
1. Change return type from `str` to `Result[T]`
2. Remove `.to_json_str()` call
3. Update callers to handle Result object
4. Update tests to use Result directly (remove `json.loads()`)

**Status:** Mandatory - Zero tolerance for violations
