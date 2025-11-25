# ADR-003: Result Pattern for Error Handling

**Date:** 2025-11-25
**Status:** Accepted
**Context:** Error and Response Handling Improvement

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
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """Result pattern for rich error handling.

    Generic result type that can hold any value type.
    """

    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    exception: Optional[Exception] = field(default=None, repr=False, compare=False)
    message: Optional[str] = None
    instruction: Optional[str] = None

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create a successful result."""
        return cls(success=True, value=value)

    @classmethod
    def failure(cls, error: str, error_type: str = "unknown", exception: Optional[Exception] = None) -> "Result[T]":
        """Create a failure result with error information."""
        return cls(success=False, error=error, error_type=error_type, exception=exception)

    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return not self.success

    def to_json(self) -> Dict[str, Any]:
        """Convert to MCP-compatible JSON format."""
        if self.success:
            result: Dict[str, Any] = {"success": True}
            if self.value is not None:
                result["value"] = self.value
        else:
            result = {
                "success": False,
                "error": self.error,
                "error_type": self.error_type,
            }
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
- **Consistent Pattern**: Uniform error handling across the system
- **Type Safety**: Generic type support for different return types
- **MCP Compatibility**: Direct JSON serialization for MCP tool responses
- **Exception Preservation**: Original exceptions stored for detailed debugging

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
