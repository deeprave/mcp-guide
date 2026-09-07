"""Template contexts expose display strings without losing structured flag values."""

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.render.cache import get_template_contexts


@pytest.mark.anyio
async def test_flag_display_and_workflow_structure_use_real_project_and_global_flags(runtime):
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"projects": {}, "feature_flags": {"autoupdate": True}})
    )
    session = await create_bound_test_session(runtime, "demo")
    phases = ["discussion", "planning", "implementation", "check", "review"]
    consent = {"planning": ["entry"], "review": ["exit"]}
    values = {"content-style": "plain", "workflow": phases, "workflow-consent": consent}
    for flag, value in values.items():
        await session.project_flags().set(flag, value)
    context = await get_template_contexts(session)

    def display(items):
        return {item["key"]: item["value"] for item in items}

    project_display = {"content-style": "plain", "workflow": str(phases), "workflow-consent": str(consent)}
    assert display(context["project"]["project_flag_values"]) == project_display
    assert display(context["feature_flag_values"]) == {"autoupdate": "true"}
    assert display(context["flag_values"]) == {"autoupdate": "true", **project_display}
    for flag, value in values.items():
        assert context["project"]["project_flags"][flag] == FeatureValue(value)
    for phase in phases:
        assert context["workflow"][phase] is True
    assert context["workflow"]["phases"]["planning"] == {"enabled": True, "next": "implementation", "ordered": True}
    assert context["workflow"]["consent"]["planning"] == {"entry": True, "exit": False, "any": True}
    assert context["workflow"]["consent"]["review"] == {"entry": False, "exit": True, "any": True}
