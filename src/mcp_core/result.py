"""Result pattern for rich error handling."""

import json
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, Optional, TypeVar

T = TypeVar("T")


__all__ = ("Result",)


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
    arguments: Optional[str] = None
    instruction: Optional[str] = None
    additional_instruction: Optional[str] = None
    error_data: Optional[dict[str, Any]] = None

    default_success_instruction: ClassVar[Optional[str]] = None
    default_failure_instruction: ClassVar[Optional[str]] = None

    @classmethod
    def success_instruction(cls) -> Optional[str]:
        return cls.default_success_instruction

    @classmethod
    def failure_instruction(cls) -> Optional[str]:
        return cls.default_failure_instruction

    @classmethod
    def ok(
        cls,
        value: Optional[T] = None,
        message: Optional[str] = None,
        arguments: Optional[str] = None,
        instruction: Optional[str] = None,
        additional_instruction: Optional[str] = None,
    ) -> "Result[T]":
        """Create a successful result.

        Args:
            value: Result value (can be None)
            message: Optional message
            arguments: Optional arguments for agent
            instruction: Optional instruction for agent
            additional_instruction: Optional side-band instruction for agent

        Returns:
            Result with success=True
        """
        return cls(
            success=True,
            value=value,
            message=message,
            arguments=arguments,
            instruction=instruction if instruction is not None else cls.default_success_instruction,
            additional_instruction=additional_instruction,
        )

    @classmethod
    def failure(
        cls,
        error: str,
        error_type: str = "unknown",
        exception: Optional[Exception] = None,
        message: Optional[str] = None,
        instruction: Optional[str] = None,
        additional_instruction: Optional[str] = None,
    ) -> "Result[T]":
        """Create a failure result with error information.

        Args:
            error: Error message
            error_type: Error classification
            exception: Original exception (optional)
            message: Optional message
            instruction: Optional instruction for agent
            additional_instruction: Optional side-band instruction for agent

        Returns:
            Result with success=False
        """
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            exception=exception,
            message=message,
            instruction=instruction if instruction is not None else cls.default_failure_instruction,
            additional_instruction=additional_instruction,
        )

    def is_ok(self) -> bool:
        """Check if result is successful.

        Returns:
            True if success, False otherwise
        """
        return self.success

    def is_failure(self) -> bool:
        """Check if result is a failure.

        Returns:
            True if failure, False otherwise
        """
        return not self.success

    def to_json(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON format.

        Returns:
            Dictionary with result data
        """
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
        if self.arguments:
            result["arguments"] = self.arguments
        if self.instruction:
            result["instruction"] = self.instruction
        if self.additional_instruction:
            result["additional_instruction"] = self.additional_instruction

        return result

    def to_json_str(self) -> str:
        """Convert to JSON string for MCP tool responses.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_json())
