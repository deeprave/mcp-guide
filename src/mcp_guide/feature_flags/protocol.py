"""Feature flags protocol definition."""

from typing import Optional, Protocol

from .types import FeatureValue


class FeatureFlags(Protocol):
    """Protocol for feature flag operations.

    This protocol provides a unified interface for both global and project-level
    feature flags, enabling polymorphic usage across different implementations.

    Implementations:
    - GlobalFlags: Manages system-wide feature flags stored in config file
    - ProjectFlags: Manages project-specific flags cached in Session

    Primary use cases:
    - Template engines: Use project flags to control rendering behavior
    - Feature gating: Enable/disable functionality based on flag values
    - Configuration management: Unified interface for flag operations

    The protocol enables future extensibility where code can work with any
    FeatureFlags implementation without knowing the specific type.
    """

    async def list(self) -> dict[str, FeatureValue]:
        """List all flags."""
        ...

    async def get(self, flag_name: str, default: Optional[FeatureValue] = None) -> Optional[FeatureValue]:
        """Get a specific flag value."""
        ...

    async def set(self, flag_name: str, value: FeatureValue) -> None:
        """Set a flag value."""
        ...

    async def remove(self, flag_name: str) -> None:
        """Remove a flag."""
        ...
