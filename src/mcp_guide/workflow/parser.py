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
