"""Feature flag type definitions."""

from typing import Any, Union

# Type alias for feature flag values
FeatureValue = Union[bool, str, list[str], dict[str, str]]

# Workflow flag names
WORKFLOW_FLAG = "workflow"
WORKFLOW_FILE_FLAG = "workflow-file"

# Client context flag names
ALLOW_CLIENT_INFO_FLAG = "allow-client-info"


def validate_feature_value_type(value: Any) -> bool:
    """Validate that a value matches FeatureValue type constraints.

    Args:
        value: Value to validate

    Returns:
        True if value is a valid FeatureValue type, False otherwise
    """
    if isinstance(value, (bool, str)):
        return True

    if isinstance(value, list):
        return all(isinstance(item, str) for item in value)

    if isinstance(value, dict):
        return all(isinstance(k, str) and isinstance(v, str) for k, v in value.items())

    return False
