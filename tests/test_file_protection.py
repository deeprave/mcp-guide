"""Tests for production file protection mechanism."""

from types import SimpleNamespace

import pytest

from .conftest import REAL_PATHS, REPO_ROOT, WorktreeFileHandler, is_gitignored


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


def test_production_guard_ignores_directory_events(monkeypatch):
    """A directory event cannot identify the file that changed."""
    from .conftest import ProductionFileHandler

    exit_called = False

    def mock_exit(*args, **kwargs):
        nonlocal exit_called
        exit_called = True

    monkeypatch.setattr(pytest, "exit", mock_exit)

    handler = ProductionFileHandler()
    handler.on_any_event(
        SimpleNamespace(
            src_path="/some/path/mcp-guide",
            dest_path="",
            event_type="modified",
            event_class="DirModifiedEvent",
            is_directory=True,
        )
    )

    assert not exit_called


def test_production_guard_reports_file_change_from_directory_event(tmp_path, monkeypatch):
    """A directory event identifies the changed protected file from its snapshot."""
    from .conftest import ProductionFileHandler

    config_file = tmp_path / "config.yaml"
    config_file.write_text("version: one\n", encoding="utf-8")
    handler = ProductionFileHandler()
    handler.watch_path(tmp_path)

    config_file.write_text("version: two\n", encoding="utf-8")
    exit_message = None

    def mock_exit(message, *args, **kwargs):
        nonlocal exit_message
        exit_message = message

    monkeypatch.setattr(pytest, "exit", mock_exit)
    handler.on_any_event(
        SimpleNamespace(
            src_path=str(tmp_path),
            dest_path="",
            event_type="modified",
            event_class="DirModifiedEvent",
            is_directory=True,
        )
    )

    assert exit_message is not None
    assert "Detected file changes:" in exit_message
    assert f"modified: {config_file}" in exit_message


def test_non_lock_file_events_trigger_exit(monkeypatch):
    """Verify non-.lock file events still terminate the test session."""
    from types import SimpleNamespace

    from .conftest import ProductionFileHandler

    exit_message = None

    def mock_exit(message, *args, **kwargs):
        nonlocal exit_message
        exit_message = message

    monkeypatch.setattr(pytest, "exit", mock_exit)

    handler = ProductionFileHandler()
    handler.on_any_event(
        SimpleNamespace(
            src_path="/some/path/config.yaml",
            dest_path="",
            event_type="modified",
            event_class="FileModifiedEvent",
            is_directory=False,
        )
    )

    assert exit_message is not None, "pytest.exit should be called for non-.lock files"
    assert "PRODUCTION FILE WRITE DETECTED" in exit_message
    assert "FileModifiedEvent" in exit_message
    assert "Path: /some/path/config.yaml" in exit_message


def test_worktree_guard_ignores_gitignored_paths(monkeypatch):
    """Gitignored worktree writes must not abort the test session."""
    exit_called = False

    def mock_exit(*args, **kwargs):
        nonlocal exit_called
        exit_called = True

    monkeypatch.setattr(pytest, "exit", mock_exit)

    ignored_dir = REPO_ROOT / "tests" / "__pycache__"
    ignored_dir.mkdir(exist_ok=True)
    ignored_file = ignored_dir / "watchdog_gitignore_sentinel.txt"
    ignored_file.write_text("gitignored write must not abort", encoding="utf-8")
    try:
        assert is_gitignored(REPO_ROOT, ignored_file)
        handler = WorktreeFileHandler(REPO_ROOT)
        handler.on_any_event(SimpleNamespace(src_path=str(ignored_file), event_type="created", is_directory=False))
        assert not exit_called, "pytest.exit should not be called for gitignored paths"
    finally:
        ignored_file.unlink(missing_ok=True)


def test_worktree_guard_ignores_directory_events_on_repo_root(monkeypatch):
    """Polling observers emit directory-modified events on the watch root."""
    exit_called = False

    def mock_exit(*args, **kwargs):
        nonlocal exit_called
        exit_called = True

    monkeypatch.setattr(pytest, "exit", mock_exit)
    handler = WorktreeFileHandler(REPO_ROOT)
    handler.on_any_event(SimpleNamespace(src_path=str(REPO_ROOT), event_type="modified", is_directory=True))
    assert not exit_called


def test_worktree_guard_aborts_on_non_ignored_fixture_write(monkeypatch):
    """A write under tests/fixtures that git would track must abort the session."""
    exit_message = None

    def mock_exit(msg, *args, **kwargs):
        nonlocal exit_message
        exit_message = msg

    monkeypatch.setattr(pytest, "exit", mock_exit)

    sentinel = REPO_ROOT / "tests" / "fixtures" / "sentinel"
    assert not is_gitignored(REPO_ROOT, sentinel)
    handler = WorktreeFileHandler(REPO_ROOT)
    handler.on_any_event(SimpleNamespace(src_path=str(sentinel), event_type="created", is_directory=False))

    assert exit_message is not None, "pytest.exit should be called for non-gitignored worktree writes"
    assert str(sentinel) in exit_message
