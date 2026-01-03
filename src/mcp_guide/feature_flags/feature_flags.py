"""Global feature flags implementation."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mcp_guide.session import Session

from .types import FeatureValue


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

    async def set(self, flag_name: str, value: FeatureValue) -> None:
        """Set a global flag value."""
        await self._session.set_feature_flag(flag_name, value)

    async def remove(self, flag_name: str) -> None:
        """Remove a global flag."""
        await self._session.remove_feature_flag(flag_name)
