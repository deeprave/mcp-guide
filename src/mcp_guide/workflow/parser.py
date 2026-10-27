"""Workflow state parsing utilities."""

from typing import Optional

import yaml
from pydantic import ValidationError

from mcp_guide.core.mcp_log import get_logger

from .flags import VALID_PHASES
from .schema import WorkflowState

logger = get_logger(__name__)


class WorkflowStateValidationError(ValueError):
    """Raised when a workflow document cannot be accepted by the workflow schema."""


def parse_workflow_state(content: str, *, raise_validation_error: bool = False) -> Optional[WorkflowState]:
    """Parse YAML content into WorkflowState model.

    Args:
        content: YAML content string

    Returns:
        WorkflowState instance if parsing succeeds, None otherwise
    """
    if not content.strip():
        if raise_validation_error:
            raise WorkflowStateValidationError("Invalid workflow file: content is empty")
        return None

    try:
        yaml_data = yaml.safe_load(content)
        if not isinstance(yaml_data, dict):
            logger.warning("Workflow content is not a valid YAML object")
            if raise_validation_error:
                raise WorkflowStateValidationError("Invalid workflow file: expected a YAML mapping")
            return None

        # Handle case-insensitive field names for all fields
        field_mappings = {
            "Phase": "phase",
            "Issue": "issue",
            "Plan": "plan",
            "Tracking": "tracking",
            "Description": "description",
            "Queue": "queue",
        }

        for cap_field, lower_field in field_mappings.items():
            if cap_field in yaml_data and lower_field not in yaml_data:
                yaml_data[lower_field] = yaml_data[cap_field]

        # Treat a YAML null queue (`queue:`) as an empty queue.
        if yaml_data.get("queue") is None:
            yaml_data["queue"] = []

        if "phase" not in yaml_data:
            logger.warning("Workflow content missing required 'phase' field")
            if raise_validation_error:
                raise WorkflowStateValidationError("Invalid workflow file: missing required `phase` field")
            return None

        # Normalize phase to lowercase for validation
        if isinstance(yaml_data["phase"], str):
            yaml_data["phase"] = yaml_data["phase"].lower()
            if yaml_data["phase"] not in VALID_PHASES:
                logger.warning("Workflow content uses an unsupported phase: %s", yaml_data["phase"])
                if raise_validation_error:
                    valid_phases = ", ".join(sorted(VALID_PHASES))
                    raise WorkflowStateValidationError(
                        f"Invalid workflow file: unsupported phase `{yaml_data['phase']}`; "
                        f"valid phases are: {valid_phases}"
                    )
                return None

        return WorkflowState.model_validate(yaml_data)
    except WorkflowStateValidationError:
        raise
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in workflow state: {e}")
        if raise_validation_error:
            raise WorkflowStateValidationError("Invalid workflow file: YAML syntax is invalid") from e
        return None
    except ValidationError as e:
        logger.warning(f"Invalid workflow state format: {e}")
        if raise_validation_error:
            tracking_error = next((error for error in e.errors() if error.get("loc") == ("tracking",)), None)
            if tracking_error is not None:
                raise WorkflowStateValidationError("Invalid workflow file: `tracking` must be a string") from e
            raise WorkflowStateValidationError("Invalid workflow file: one or more fields have invalid values") from e
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing workflow state: {e}")
        if raise_validation_error:
            raise WorkflowStateValidationError("Invalid workflow file: unable to process content") from e
        return None
