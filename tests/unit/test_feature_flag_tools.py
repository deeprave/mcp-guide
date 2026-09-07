"""Project flag tool behaviour through real configuration and scope resolution."""

import pytest
from tests.helpers import create_bound_test_session, create_unbound_test_session, request_context_for

from mcp_guide.tools.tool_feature_flags import (
    GetFlagArgs,
    ListFlagsArgs,
    SetFlagArgs,
    internal_get_project_flag,
    internal_list_project_flags,
    internal_set_project_flag,
)


@pytest.fixture
async def flag_context(runtime, tmp_path):
    config_dir = tmp_path
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text("feature_flags: {}\nprojects: {}\n")
    session = await create_bound_test_session(runtime, "flags")
    return await request_context_for(session)


@pytest.mark.anyio
async def test_listing_flags_without_a_bound_project_returns_guidance(runtime):
    context = await request_context_for(create_unbound_test_session(runtime))
    result = await internal_list_project_flags(ListFlagsArgs(), context)
    assert not result.success
    assert result.error_type == "no_project"
    assert "No project available" in result.error


@pytest.mark.anyio
async def test_flag_resolution_keeps_project_overrides_and_global_fallback(runtime, flag_context):
    global_flags = runtime.feature_flags()
    await global_flags.set("global_flag", True)
    await global_flags.set("shared_flag", "global_value")
    project_flags = flag_context.session.project_flags()
    await project_flags.set("project_flag", False)
    await project_flags.set("shared_flag", "project_override")
    await project_flags.set("workflow", ["discussion", "implementation"])
    project = await project_flags.list()
    for active, expected in ((False, project), (True, {"global_flag": True, **project})):
        result = await internal_list_project_flags(ListFlagsArgs(active=active), flag_context)
        assert result.success
        assert result.value == expected
    selected = await internal_list_project_flags(ListFlagsArgs(feature_name="workflow"), flag_context)
    assert selected.success
    assert selected.value == ["discussion", "implementation"]
    for name, expected in (("global_flag", True), ("shared_flag", "project_override"), ("missing", None)):
        result = await internal_get_project_flag(GetFlagArgs(feature_name=name), flag_context)
        assert result.success
        assert result.value == expected


@pytest.mark.anyio
async def test_setting_default_explicit_and_removed_flags_changes_configuration(flag_context):
    for kwargs, expected, message in (
        ({}, True, "Flag 'test_flag' set to True"),
        ({"value": "custom_value"}, "custom_value", "Flag 'test_flag' set to 'custom_value'"),
        ({"value": None}, None, "Flag 'test_flag' removed"),
    ):
        result = await internal_set_project_flag(SetFlagArgs(feature_name="test_flag", **kwargs), flag_context)
        assert result.success
        assert result.value == message
        flags = await flag_context.session.project_flags().list()
        assert flags == ({"test_flag": expected} if expected is not None else {})
    invalid = await internal_set_project_flag(SetFlagArgs(feature_name="invalid.flag"), flag_context)
    assert not invalid.success
    assert invalid.error_type == "validation_error"
    assert "periods" in invalid.error
    assert await flag_context.session.project_flags().list() == {}
