"""Stable project identities and round-trippable hash-suffixed keys."""

import pytest

from mcp_guide.utils.project_hash import calculate_project_hash, extract_name_from_key, generate_project_key


def test_hash_is_stable_lexically_normalised_and_distinguishes_roots():
    root = "/client/my-project"
    identity = calculate_project_hash(root)
    assert len(identity) == 64
    assert identity == calculate_project_hash(root)
    # Pass the lexical spelling directly; Path would remove "." before the function sees it.
    assert identity == calculate_project_hash("/client/./parent/../my-project/")
    assert identity != calculate_project_hash("/other/my-project")


def test_hash_preserves_client_symlink_identity(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    client_link = tmp_path / "client-link"
    client_link.symlink_to(target, target_is_directory=True)
    assert calculate_project_hash(str(client_link)) != calculate_project_hash(str(target))


@pytest.mark.parametrize("name", ["my-project", "my-complex-project-name"])
def test_project_key_round_trip_keeps_name_and_eight_hash_characters(name):
    key = generate_project_key(name, "abcdef1234567890" * 4)
    assert key == f"{name}-abcdef12"
    assert extract_name_from_key(key) == name
