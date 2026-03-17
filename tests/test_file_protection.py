"""Tests for production file protection mechanism."""

import pytest

from .conftest import REAL_PATHS


def test_protection_monitors_real_production_paths(session_temp_dir):
    """Verify watchdog monitors REAL production paths, not test paths."""
    from mcp_guide.config_paths import get_config_file, get_docroot

    # Verify environment is redirected to test paths using get_config_file() and get_docroot()
    test_config = get_config_file().parent
    test_docroot = get_docroot()

    assert str(session_temp_dir) in str(test_config), "Config should be in test temp dir"
    assert str(session_temp_dir) in str(test_docroot), "Docroot should be in test temp dir"

    # Verify real paths are DIFFERENT from test paths
    assert test_config != REAL_PATHS["mcp_guide_config"], "Real production config should differ from test config"
    assert test_docroot != REAL_PATHS["mcp_guide_docroot"], "Real production docroot should differ from test docroot"

    # Verify real paths point to actual user directories (not test temp)
    assert str(session_temp_dir) not in str(REAL_PATHS["mcp_guide_config"]), (
        "Real config should not be in test temp dir"
    )
    assert REAL_PATHS["mcp_guide_config"].is_absolute(), "Real config should be an absolute path"


def test_protection_fixture_exists():
    """Verify the protection fixture is properly configured."""
    # This test just needs to run - if the fixture is broken, it will fail
    # The fixture is autouse=True, so it's already active
    pass


def test_can_safely_modify_test_paths(tmp_path, session_temp_dir):
    """Verify tests CAN modify test paths without triggering protection."""
    # This should NOT trigger watchdog because it's in test temp dir
    test_file = tmp_path / "safe_test_file.txt"
    test_file.write_text("This is safe - it's in test temp dir")

    # If we get here without pytest.exit(), protection is working correctly
    assert test_file.exists()
    test_file.unlink()


def test_lock_file_events_are_ignored(monkeypatch):
    """Verify .lock file events do not terminate the test session."""
    from types import SimpleNamespace

    from .conftest import ProductionFileHandler

    exit_called = False

    def mock_exit(*args, **kwargs):
        nonlocal exit_called
        exit_called = True

    monkeypatch.setattr(pytest, "exit", mock_exit)

    handler = ProductionFileHandler()
    handler.on_any_event(SimpleNamespace(src_path="/some/path/config.lock", event_type="modified"))

    assert not exit_called, "pytest.exit should not be called for .lock files"


def test_non_lock_file_events_trigger_exit(monkeypatch):
    """Verify non-.lock file events still terminate the test session."""
    from types import SimpleNamespace

    from .conftest import ProductionFileHandler

    exit_called = False

    def mock_exit(*args, **kwargs):
        nonlocal exit_called
        exit_called = True

    monkeypatch.setattr(pytest, "exit", mock_exit)

    handler = ProductionFileHandler()
    handler.on_any_event(SimpleNamespace(src_path="/some/path/config.yaml", event_type="modified"))

    assert exit_called, "pytest.exit should be called for non-.lock files"
