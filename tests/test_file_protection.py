"""Tests for production file protection mechanism."""

from pathlib import Path

import conftest
import pytest


def test_protection_monitors_real_production_paths(session_temp_dir):
    """Verify watchdog monitors REAL production paths, not test paths."""
    from mcp_guide.config_paths import get_config_file, get_docroot

    # Verify environment is redirected to test paths using get_config_file() and get_docroot()
    test_config = get_config_file().parent
    test_docroot = get_docroot()

    assert str(session_temp_dir) in str(test_config), "Config should be in test temp dir"
    assert str(session_temp_dir) in str(test_docroot), "Docroot should be in test temp dir"

    # Verify real paths are DIFFERENT from test paths
    assert test_config != conftest._REAL_MCP_GUIDE_CONFIG, "Real production config should differ from test config"
    assert test_docroot != conftest._REAL_MCP_GUIDE_DOCROOT, "Real production docroot should differ from test docroot"

    # Verify real paths point to actual user directories (not test temp)
    assert str(session_temp_dir) not in str(conftest._REAL_MCP_GUIDE_CONFIG), (
        "Real config should not be in test temp dir"
    )
    assert conftest._REAL_MCP_GUIDE_CONFIG.is_absolute(), "Real config should be an absolute path"


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
