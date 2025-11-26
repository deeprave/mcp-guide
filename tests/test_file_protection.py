"""Tests for production file protection mechanism."""

from pathlib import Path

import conftest
import pytest


def test_protection_monitors_real_production_paths(session_temp_dir):
    """Verify watchdog monitors REAL production paths, not test paths."""
    from mcp_guide.config_paths import get_default_config_file, get_default_docroot

    # Verify environment is redirected to test paths
    test_config = get_default_config_file().parent
    test_docroot = get_default_docroot()

    assert str(session_temp_dir) in str(test_config), "Config should be in test temp dir"
    assert str(session_temp_dir) in str(test_docroot), "Docroot should be in test temp dir"

    # Verify real paths are DIFFERENT from test paths
    assert test_config != conftest._REAL_MCP_GUIDE_CONFIG, "Real production config should differ from test config"
    assert test_docroot != conftest._REAL_MCP_GUIDE_DOCROOT, "Real production docroot should differ from test docroot"

    # Verify real paths point to actual user directories (not test temp)
    assert str(conftest._REAL_HOME) in str(conftest._REAL_MCP_GUIDE_CONFIG) or "AppData" in str(
        conftest._REAL_MCP_GUIDE_CONFIG
    ), "Real config should be in real user home or AppData"


def test_protection_fixture_exists():
    """Verify the protection fixture is properly configured."""
    # This test just needs to run - if the fixture is broken, it will fail
    # The fixture is autouse=True, so it's already active
    pass


def test_can_safely_modify_test_paths(isolated_config_file, session_temp_dir):
    """Verify tests CAN modify test paths without triggering protection."""
    # This should NOT trigger watchdog because it's in test temp dir
    test_file = isolated_config_file.parent / "safe_test_file.txt"
    test_file.write_text("This is safe - it's in test temp dir")

    # If we get here without pytest.exit(), protection is working correctly
    assert test_file.exists()
    test_file.unlink()
