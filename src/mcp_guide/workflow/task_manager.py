"""Workflow task manager for coordinating workflow tasks with TaskManager."""

from pathlib import Path
from typing import Any, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.models import FileReadError, NoProjectError
from mcp_guide.session import get_current_session
from mcp_guide.task_manager import EventType, TaskManager, get_task_manager
from mcp_guide.utils.system_content import render_system_content
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE, WORKFLOW_DIR
from mcp_guide.workflow.tasks import WORKFLOW_INTERVAL, WorkflowMonitorTask

logger = get_logger(__name__)


class WorkflowTaskManager:
    """Manages workflow task lifecycle and configuration changes."""

    def __init__(self, task_manager: Optional[TaskManager] = None):
        self._task_manager = get_task_manager()

    async def manage_workflow_task(self) -> None:
        """Manage workflow task based on current project configuration changes."""
        logger.trace("Starting workflow task management")
        try:
            session = get_current_session()
            if not session:
                logger.trace("No session available for workflow task management")
                return

            # Get workflow configuration
            project_flags = session.project_flags()
            workflow_file_flag = await project_flags.get("workflow-file")
            workflow_file = workflow_file_flag if isinstance(workflow_file_flag, str) else DEFAULT_WORKFLOW_FILE
            workflow_enabled = True  # Always enabled, using default file if no explicit flag

            logger.trace(f"Workflow configuration: file={workflow_file}, enabled={workflow_enabled}")

            # Check if workflow task is already subscribed
            has_running_task = any(
                isinstance(sub.subscriber_ref(), WorkflowMonitorTask)
                for sub in self._task_manager._subscriptions
                if sub.subscriber_ref() is not None and sub.event_types & EventType.TIMER
            )

            logger.trace(f"Has running workflow task: {has_running_task}")

            # Start task if no task is running and workflow is enabled
            start_new = not has_running_task and workflow_enabled and bool(workflow_file)

            logger.trace(f"Should start new task: {start_new}")

            if start_new:
                logger.trace(f"Creating WorkflowMonitorTask for file: {workflow_file}")
                # Start new workflow task
                task = WorkflowMonitorTask(workflow_file, self._task_manager)
                logger.trace(f"Subscribing WorkflowMonitorTask: {task}")
                await self._task_manager.subscribe(task, EventType.TIMER | EventType.FS_FILE_CONTENT, WORKFLOW_INTERVAL)
                logger.trace("WorkflowMonitorTask subscribed successfully")

                # Queue setup instruction
                try:
                    content = await self.render_workflow_template("monitoring-setup")
                    await self._task_manager.queue_instruction(content)
                    logger.trace("Workflow setup instruction queued")
                except (NoProjectError, FileReadError) as e:
                    logger.warning(f"Workflow setup failed due to configuration issue: {e}")
                    # Don't continue with workflow management if basic setup fails
                    return
                except Exception as e:
                    logger.error(f"Failed to queue workflow setup instruction: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Workflow management failed: {e}", exc_info=True)

    @staticmethod
    async def render_workflow_template(template_pattern: str) -> str:
        """Render workflow template and return the content.

        Raises:
            NoProjectError: If no session is available for workflow template rendering
        """
        logger.trace(f"render_workflow_template called with template_pattern: {template_pattern}")
        session = get_current_session()
        if not session:
            raise NoProjectError("No session available for workflow template rendering")

        logger.trace("Session found, getting docroot")
        docroot = Path(await session.get_docroot())
        workflow_dir = docroot / WORKFLOW_DIR

        # Get template context for rendering
        logger.trace("Getting template contexts")
        context = await get_template_contexts()

        logger.trace(f"Rendering system content for pattern: {template_pattern}")
        result = await render_system_content(
            system_dir=workflow_dir, pattern=template_pattern, context=context, docroot=docroot
        )

        if not result.success or not result.value:
            error_msg = result.error if not result.success else "Empty result"
            raise FileReadError(f"Failed to render workflow template: {error_msg}")

        logger.trace(f"System content rendered successfully: {len(result.value)} chars")
        return result.value

    async def _queue_workflow_setup_instruction(self, session: Any, workflow_file: str) -> None:
        """Queue workflow setup instruction using system content rendering."""
        try:
            content = await self.render_workflow_template("monitoring-setup")
            await self._task_manager.queue_instruction(content)
        except (NoProjectError, FileReadError) as e:
            logger.warning(f"Workflow setup failed due to configuration issue: {e}")
        except Exception as e:
            logger.error(f"Failed to queue workflow setup instruction: {e}", exc_info=True)
