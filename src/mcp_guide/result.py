from mcp_guide.core.result import Result
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY, INSTRUCTION_ERROR_MESSAGE

__all__ = ("Result",)

# Set default instructions for the guide application
if Result.default_success_instruction is None:
    Result.default_success_instruction = INSTRUCTION_DISPLAY_ONLY
if Result.default_failure_instruction is None:
    Result.default_failure_instruction = INSTRUCTION_ERROR_MESSAGE
