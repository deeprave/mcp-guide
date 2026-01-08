"""Prompt decorator for FastMCP with configurable prefixes."""

import os
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, Type

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager
    from mcp_guide.workflow.task_manager import WorkflowTaskManager

from mcp.server import FastMCP

from mcp_core.arguments import Arguments
from mcp_core.mcp_log import get_logger
from mcp_core.result import Result

logger = get_logger(__name__)

# Global TaskManager instance for result processing
_task_manager: Optional["TaskManager"] = None
_workflow_task_manager: Optional["WorkflowTaskManager"] = None


def set_workflow_task_manager(workflow_task_manager: "WorkflowTaskManager") -> None:
    """Set the global WorkflowTaskManager instance."""
    global _workflow_task_manager
    _workflow_task_manager = workflow_task_manager


def _log_prompt_result(prompt_name: str, result: Any) -> None:
    """Log prompt result for debugging."""
    if isinstance(result, Result):
        logger.trace(
            f"RESULT: Prompt {prompt_name} returning result",
            extra={"message": "Returning result", "result": result.to_json()},
        )


def set_task_manager(task_manager: Optional["TaskManager"]) -> None:
    """Set the global TaskManager instance for result processing.

    Args:
        task_manager: TaskManager instance or None to clear
    """
    global _task_manager, _workflow_task_manager
    from mcp_guide.task_manager import get_task_manager

    _task_manager = get_task_manager() if task_manager is not None else None

    if task_manager:
        from mcp_guide.workflow.task_manager import WorkflowTaskManager

        _workflow_task_manager = WorkflowTaskManager(task_manager)
    else:
        _workflow_task_manager = None


async def _manage_workflow_task() -> None:
    """Delegate workflow management to dedicated manager."""
    if _workflow_task_manager:
        await _workflow_task_manager.manage_workflow_task()


async def _process_prompt_result(result: "Result[Any]", prompt_name: str) -> "Result[Any]":
    """Process prompt result through TaskManager."""
    # If result is a Result object, process it
    if isinstance(result, Result):
        # Process through TaskManager if available
        if _task_manager is not None:
            try:
                result = await _task_manager.process_result(result)
            except Exception as e:
                logger.error(f"TaskManager processing failed for prompt {prompt_name}: {e}")

        # Manage workflow tasks after prompt execution
        try:
            await _manage_workflow_task()
        except Exception as e:
            logger.error(f"Workflow task management failed after prompt {prompt_name}: {e}")

    return result


class ExtMcpPromptDecorator:
    """Prompt decorator that adds configurable prefixes and handles Arguments classes.

    Similar to ExtMcpToolDecorator but for prompts. Reads MCP_PROMPT_PREFIX environment
    variable and defaults to empty string (no prefix).
    """

    def __init__(self, mcp: FastMCP) -> None:
        """Initialize prompt decorator.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.prefix = os.environ.get("MCP_PROMPT_PREFIX", "")

    def prompt(
        self,
        args_class: Optional[Type[Arguments]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a prompt function for FastMCP registration.

        Args:
            args_class: Arguments subclass (auto-generates description)
            name: Override prompt name
            description: Override prompt description

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Determine final name
            final_name = name or func.__name__
            if self.prefix:
                final_name = f"{self.prefix}_{final_name}"

            # Build description
            if args_class is not None and description is None:
                final_description = args_class.build_description(func)
            else:
                final_description = description or func.__doc__ or ""

            # Wrap function to add result processing
            @wraps(func)
            async def wrapped_func(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                result = await _process_prompt_result(result, final_name)
                _log_prompt_result(final_name, result)
                return result

            # Register with FastMCP
            self.mcp.prompt(name=final_name, description=final_description)(wrapped_func)

            return func

        return decorator
