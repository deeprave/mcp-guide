"""Behavioural tests for global OpenSpec feature-flag state."""

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.openspec.state import parse_openspec_state, serialise_openspec_state


def test_absent_openspec_state_is_unknown_and_does_not_serialise() -> None:
    """An absent global flag has no CLI result until an enabled project checks it."""
    state = parse_openspec_state(None)

    assert state.validated is None
    assert state.version is None
    assert state.checked is None
    assert serialise_openspec_state(state) is None


def test_completed_valid_check_round_trips_through_structured_flag() -> None:
    """A parsed CLI result retains its validation, version, and check time."""
    state = parse_openspec_state(FeatureValue({"validated": "true", "version": "1.10.0", "checked": "100.5"}))

    assert state.validated is True
    assert state.version == "1.10.0"
    assert state.checked == 100.5
    assert serialise_openspec_state(state) == {"validated": "true", "version": "1.10.0", "checked": "100.5"}


def test_invalid_check_omits_version_but_records_time() -> None:
    """Failed checks are retained to throttle repeated availability prompts."""
    state = parse_openspec_state(FeatureValue({"validated": "false", "checked": "100.0"}))

    assert state.validated is False
    assert state.version is None
    assert serialise_openspec_state(state) == {"validated": "false", "checked": "100.0"}


def test_non_finite_check_timestamp_is_invalid() -> None:
    """A check timestamp must be a finite UTC Unix timestamp."""
    assert parse_openspec_state(FeatureValue({"validated": "true", "checked": "nan"})).validated is None
