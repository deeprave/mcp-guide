"""Configuration file model."""

from dataclasses import field

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from mcp_guide.feature_flags.types import FeatureValue


@pydantic_dataclass(frozen=True)
class ConfigFile:
    """Configuration file structure with feature flags.

    Attributes:
        feature_flags: Dictionary of global feature flags with FeatureValue types
        docroot: Document root directory path

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
        Feature flag names and values are validated.
    """

    model_config = ConfigDict(extra="ignore")

    feature_flags: dict[str, FeatureValue] = field(default_factory=dict)
    docroot: str = ""

    @field_validator("feature_flags")
    @classmethod
    def validate_feature_flags(cls, v: dict[str, FeatureValue]) -> dict[str, FeatureValue]:
        from mcp_guide.feature_flags.validators import validate_flag_name, validate_flag_value

        for flag_name, flag_value in v.items():
            if not validate_flag_name(flag_name):
                raise ValueError(f"Invalid feature flag name: {flag_name}")
            if not validate_flag_value(flag_value):
                raise ValueError(f"Invalid feature flag value type for '{flag_name}': {type(flag_value)}")
        return v
