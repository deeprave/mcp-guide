"""Feature-value resolution respects project precedence and registered scopes."""

from mcp_guide.feature_flags.constants import FLAG_OPENSPEC, FLAG_OPENSPEC_STATE
from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.feature_flags.types import FeatureValue


def test_generic_flags_prefer_project_values_then_global_then_absence():
    project = {
        "boolean": FeatureValue(False),
        "list": FeatureValue(["project"]),
        "text": FeatureValue("project text"),
    }
    global_flags = {
        "boolean": FeatureValue(True),
        "list": FeatureValue(["global"]),
        "mapping": FeatureValue({"key": "value"}),
    }
    for key in project:
        assert resolve_flag(key, project, global_flags) is project[key]
    assert resolve_flag("mapping", project, global_flags) is global_flags["mapping"]
    assert resolve_flag("missing", project, global_flags) is None
    assert resolve_flag("missing", {}, {}) is None


def test_project_only_flag_does_not_fall_back_to_global():
    assert resolve_flag(FLAG_OPENSPEC, {}, {FLAG_OPENSPEC: FeatureValue(True)}) is None


def test_feature_only_flag_cannot_be_shadowed_by_project():
    global_value = FeatureValue({"validated": "true", "checked": "100"})
    assert (
        resolve_flag(
            FLAG_OPENSPEC_STATE, {FLAG_OPENSPEC_STATE: FeatureValue("project")}, {FLAG_OPENSPEC_STATE: global_value}
        )
        is global_value
    )
