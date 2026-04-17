"""Global feature flags implementation."""

from typing import TYPE_CHECKING, Optional, cast

from pydantic_core import InitErrorDetails, ValidationError

from mcp_guide.feature_flags.validators import normalise_flag, validate_flag_with_registered

if TYPE_CHECKING:
    from mcp_guide.session import Session

from .types import FeatureValue, RawFeatureValue


def _invalid_feature_value_error(value: object) -> ValidationError:
    """Build a consistent validation error for unsupported feature flag values."""
    line_error = cast(
        InitErrorDetails,
        {
            "type": "value_error",
            "loc": ("value",),
            "input": value,
            "ctx": {"error": "Invalid feature flag value"},
        },
    )
    return ValidationError.from_exception_data(
        "FeatureValue",
        [line_error],
    )


class FeatureFlags:
    """Global feature flags implementation that proxies Session."""

    def __init__(self, session: "Session"):
        self._session = session

    async def list(self) -> dict[str, FeatureValue]:
        """List all global flags."""
        return await self._session.get_feature_flags()

    async def get(self, flag_name: str, default: Optional[FeatureValue] = None) -> Optional[FeatureValue]:
        """Get a specific global flag value."""
        flags = await self.list()
        return flags.get(flag_name, default)

    async def set(self, flag_name: str, value: RawFeatureValue | FeatureValue) -> None:
        """Set a global flag value."""
        try:
            wrapped_value = FeatureValue.from_raw(value)
        except TypeError as exc:
            raise _invalid_feature_value_error(value) from exc
        normalised_value = normalise_flag(flag_name, wrapped_value)
        if normalised_value is None:
            raise ValueError(f"Flag `{flag_name}` normalised to None; use remove() instead")
        validate_flag_with_registered(flag_name, normalised_value, is_project=False)
        await self._session.set_feature_flag(flag_name, normalised_value)

    async def remove(self, flag_name: str) -> None:
        """Remove a global flag."""
        await self._session.remove_feature_flag(flag_name)
