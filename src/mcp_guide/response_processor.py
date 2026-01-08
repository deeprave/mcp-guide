"""Response processing extension for global additional_agent_instructions injection."""

from typing import TYPE_CHECKING, Any, Callable, Optional

from mcp_core.mcp_log import get_logger

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)


def process_response_for_instructions(response: Any, task_manager: Optional["TaskManager"] = None) -> Any:
    """Process response and inject additional instructions if available.

    Args:
        response: The response from agent interaction
        task_manager: TaskManager instance for instruction processing

    Returns:
        Response with potential additional_agent_instructions injection
    """
    if task_manager is None:
        return response

    # Check if TaskManager has pending instructions
    if not hasattr(task_manager, "_pending_instructions"):
        return response

    if not task_manager._pending_instructions:
        return response

    # Get next instruction (FIFO)
    instruction = task_manager._pending_instructions.pop(0)

    # Try to inject instruction into response
    try:
        if isinstance(response, dict):
            # Create a copy to avoid modifying the original
            response_copy = response.copy()
            if (
                "additional_agent_instructions" not in response_copy
                or response_copy["additional_agent_instructions"] is None
            ):
                response_copy["additional_agent_instructions"] = instruction
                logger.debug(f"Injected instruction into response: {instruction}")
                return response_copy
        elif isinstance(response, str):
            # If response is a string, append instruction
            response = f"{response}\n\n[Additional instruction: {instruction}]"
            logger.debug(f"Appended instruction to string response: {instruction}")
        else:
            # For other response types, log that we couldn't inject
            logger.debug(f"Could not inject instruction into response type {type(response)}: {instruction}")
            # Put instruction back for next response
            task_manager._pending_instructions.insert(0, instruction)
    except Exception as e:
        logger.warning(f"Failed to inject instruction, returning original response: {e}")
        # Put instruction back for next response
        task_manager._pending_instructions.insert(0, instruction)

    return response


def create_instrumented_sample_function(
    original_sample: Callable[..., Any], task_manager: Optional["TaskManager"] = None
) -> Callable[..., Any]:
    """Create an instrumented version of the sample function that processes responses.

    Args:
        original_sample: The original sample function to wrap
        task_manager: TaskManager instance for instruction processing

    Returns:
        Wrapped sample function with response processing
    """

    async def instrumented_sample(*args: Any, **kwargs: Any) -> Any:
        """Wrapped sample function with response processing."""
        try:
            # Call original sample function
            response = await original_sample(*args, **kwargs)

            # Process response for instruction injection
            processed_response = process_response_for_instructions(response, task_manager)

            return processed_response

        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Response processing failed, falling back to original: {e}")
            return await original_sample(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error in instrumented sample function: {e}")
            raise

    return instrumented_sample
