"""Feature flag type definitions."""

from typing import Any, TypeAlias

FeatureScalar: TypeAlias = bool | str
FeatureList: TypeAlias = list[str]
FeatureDictValue: TypeAlias = str | list[str]

# Type alias for feature flag values
FeatureValue: TypeAlias = FeatureScalar | FeatureList | dict[str, FeatureDictValue]


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
        return all(
            isinstance(key, str)
            and (isinstance(item, str) or (isinstance(item, list) and all(isinstance(entry, str) for entry in item)))
            for key, item in value.items()
        )

    return False
