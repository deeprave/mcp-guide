"""Workflow state parsing utilities."""

from typing import Optional

import yaml
from pydantic import ValidationError

from mcp_core.mcp_log import get_logger

from .schema import WorkflowState

logger = get_logger(__name__)


def parse_workflow_state(content: str) -> Optional[WorkflowState]:
    """Parse YAML content into WorkflowState model.

    Args:
        content: YAML content string

    Returns:
        WorkflowState instance if parsing succeeds, None otherwise
    """
    if not content.strip():
        return None

    try:
        yaml_data = yaml.safe_load(content)
        if not isinstance(yaml_data, dict):
            logger.warning("Workflow content is not a valid YAML object")
            return None

        # Handle case-insensitive field names for all fields
        field_mappings = {
            "Phase": "phase",
            "Issue": "issue",
            "Tracking": "tracking",
            "Description": "description",
            "Queue": "queue",
        }

        for cap_field, lower_field in field_mappings.items():
            if cap_field in yaml_data and lower_field not in yaml_data:
                yaml_data[lower_field] = yaml_data[cap_field]

        if "phase" not in yaml_data:
            logger.warning("Workflow content missing required 'phase' field")
            return None

        # Normalize phase to lowercase for validation
        if isinstance(yaml_data["phase"], str):
            yaml_data["phase"] = yaml_data["phase"].lower()

        return WorkflowState.model_validate(yaml_data)
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in workflow state: {e}")
        return None
    except ValidationError as e:
        logger.warning(f"Invalid workflow state format: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing workflow state: {e}")
        return None
