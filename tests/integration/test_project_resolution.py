"""Resolve real root hashes without confusing same-named project configurations."""

import pytest
import yaml

from mcp_guide.session import bind_session_project
from mcp_guide.utils.project_hash import calculate_project_hash, generate_project_key
from tests.helpers import create_unbound_test_session


@pytest.mark.anyio
async def test_same_named_roots_select_exact_configuration_and_create_only_missing_roots(runtime, tmp_path):
    roots = [tmp_path / owner / "my-project" for owner in ("first", "second", "new")]
    hashes = [calculate_project_hash(str(root)) for root in roots]
    keys = [generate_project_key("my-project", value) for value in hashes]
    projects = {
        key: {
            "name": "my-project",
            "hash": root_hash,
            "categories": {},
            "collections": {},
            "project_flags": {"owner": owner},
        }
        for key, root_hash, owner in zip(keys[:2], hashes[:2], ("first", "second"))
    }
    config_file = runtime.configuration_service().config_file
    config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path / "docs"), "projects": projects}))

    for index, owner in ((1, "second"), (0, "first")):
        session = create_unbound_test_session(runtime)
        project = await bind_session_project(session, roots[index])
        assert project.name == "my-project"
        assert project.key == keys[index]
        assert project.hash == hashes[index]
        assert project.project_flags == {"owner": owner}

    session = create_unbound_test_session(runtime)
    project = await bind_session_project(session, roots[2])
    assert project.name == "my-project"
    assert project.key == keys[2]
    assert project.hash == hashes[2]
    assert project.project_flags == {}
    stored = yaml.safe_load(config_file.read_text())["projects"]
    assert set(stored) == set(keys)
    assert stored[keys[0]] == projects[keys[0]]
    assert stored[keys[1]] == projects[keys[1]]
