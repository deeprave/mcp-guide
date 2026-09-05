"""Structured global feature-flag state for OpenSpec CLI checks."""

from dataclasses import dataclass
from math import isfinite

from mcp_guide.feature_flags.types import FeatureValue


@dataclass(frozen=True)
class OpenSpecState:
    """The parsed machine-wide result of an OpenSpec CLI check."""

    validated: bool | None = None
    version: str | None = None
    checked: float | None = None


def parse_openspec_state(value: FeatureValue | None) -> OpenSpecState:
    """Parse a structured feature flag without treating malformed data as valid."""
    raw = value.to_raw() if value is not None else None
    if not isinstance(raw, dict):
        return OpenSpecState()

    validated = raw.get("validated")
    checked = raw.get("checked")
    version = raw.get("version")
    if validated not in {"true", "false"} or not isinstance(checked, str):
        return OpenSpecState()
    try:
        checked_at = float(checked)
    except ValueError:
        return OpenSpecState()
    if not isfinite(checked_at):
        return OpenSpecState()
    if not isinstance(version, str) and version is not None:
        return OpenSpecState()
    return OpenSpecState(validated=validated == "true", version=version, checked=checked_at)


def serialise_openspec_state(state: OpenSpecState) -> dict[str, str] | None:
    """Return the complete flag value, omitting unknown state."""
    if state.validated is None or state.checked is None:
        return None
    value = {"validated": str(state.validated).lower(), "checked": str(state.checked)}
    if state.version is not None:
        value["version"] = state.version
    return value
