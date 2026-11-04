"""Startup client-filesystem sharing for the inherited-PWD opt-in."""

import pytest

from mcp_guide.session import initial_filesystem_sharing


@pytest.fixture
def server_directory(temp_project_dir, monkeypatch):
    """Run the server process in a real directory whose PWD agrees with it."""
    monkeypatch.chdir(temp_project_dir)
    monkeypatch.setenv("PWD", str(temp_project_dir))
    return temp_project_dir


def test_opted_in_stdio_with_matching_pwd_is_shared_immediately(server_directory):
    """The probe is unnecessary when PWD is the server's own working directory."""
    assert initial_filesystem_sharing("stdio", True) is True


def test_symlinked_pwd_for_the_same_directory_is_accepted(server_directory, temp_project_dir, monkeypatch):
    """PWD is the logical path; a symlink to the physical working directory still matches."""
    link = temp_project_dir.parent / f"{server_directory.name}-link"
    link.symlink_to(server_directory, target_is_directory=True)
    monkeypatch.setenv("PWD", str(link))

    assert initial_filesystem_sharing("stdio", True) is True


def test_stdio_without_the_opt_in_stays_unverified(server_directory, monkeypatch):
    """Without --use-pwd or MG_USE_PWD the probe decides, exactly as before."""
    monkeypatch.delenv("MG_USE_PWD", raising=False)

    assert initial_filesystem_sharing("stdio", False) is None


def test_environment_opt_in_is_equivalent_to_the_flag(server_directory, monkeypatch):
    """MG_USE_PWD=1 opts in even when the configuration object did not carry --use-pwd."""
    monkeypatch.setenv("MG_USE_PWD", "1")

    assert initial_filesystem_sharing("stdio", False) is True


@pytest.mark.parametrize("transport", ["http", "https"])
def test_remote_transports_are_never_shared(server_directory, transport):
    """The opt-in never applies outside stdio, even with a matching PWD."""
    assert initial_filesystem_sharing(transport, True) is False


def test_unset_pwd_leaves_sharing_unverified(server_directory, monkeypatch):
    """Without PWD there is no evidence of the server's directory."""
    monkeypatch.delenv("PWD")

    assert initial_filesystem_sharing("stdio", True) is None


@pytest.mark.parametrize(
    "pwd_for",
    [
        lambda directory: "",
        lambda directory: "relative/path",
        lambda directory: str(directory / "missing"),
        lambda directory: str(directory.parent),
    ],
    ids=["empty", "relative", "missing-directory", "different-directory"],
)
def test_pwd_that_is_not_the_server_directory_leaves_sharing_unverified(server_directory, monkeypatch, pwd_for):
    """A PWD that is not evidence of the server's own directory is ignored."""
    monkeypatch.setenv("PWD", pwd_for(server_directory))

    assert initial_filesystem_sharing("stdio", True) is None


def test_pwd_naming_a_file_is_not_a_directory(server_directory, monkeypatch):
    """A PWD that exists but is not a directory is not evidence."""
    not_a_directory = server_directory / "file.txt"
    not_a_directory.write_text("x")
    monkeypatch.setenv("PWD", str(not_a_directory))

    assert initial_filesystem_sharing("stdio", True) is None
