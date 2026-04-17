"""Tests for feature flag type system."""

import pytest

from mcp_guide.feature_flags.types import (
    FeatureValue,
    format_feature_value_for_display,
    to_raw_feature_value,
    validate_feature_value_type,
)


class TestFeatureValueType:
    """Test FeatureValue wrapper and validation."""

    def test_feature_value_constructs_from_valid_raw_values(self):
        assert FeatureValue(True).to_raw() is True
        assert FeatureValue("test").to_raw() == "test"
        assert FeatureValue(["a", "b"]).to_raw() == ["a", "b"]
        assert FeatureValue({"key": "value"}).to_raw() == {"key": "value"}

    def test_feature_value_rejects_invalid_raw_values(self):
        with pytest.raises(TypeError):
            FeatureValue(123)
        with pytest.raises(TypeError):
            FeatureValue({"key": 123})

    def test_feature_value_display_formatting(self):
        assert FeatureValue(True).to_display() == "true"
        assert FeatureValue("plain").to_display() == "plain"
        assert FeatureValue(["discussion", "implementation"]).to_display() == "['discussion', 'implementation']"
        assert FeatureValue({"implementation": ["entry"]}).to_display() == "{'implementation': ['entry']}"

    def test_feature_value_contains_matches_underlying_container_semantics(self):
        assert "discussion" in FeatureValue(["discussion", "implementation"])
        assert "phase" in FeatureValue({"phase": "entry"})
        assert "la" in FeatureValue("plain")
        assert 1 not in FeatureValue("plain")

    def test_feature_value_repr_includes_wrapper_type(self):
        assert repr(FeatureValue("plain")) == "FeatureValue('plain')"

    def test_to_raw_feature_value_accepts_wrapped_or_raw(self):
        wrapped = FeatureValue(["a", "b"])
        assert to_raw_feature_value(wrapped) == ["a", "b"]
        assert to_raw_feature_value(True) is True

    def test_validate_feature_value_type_accepts_valid_types(self):
        assert validate_feature_value_type(True) is True
        assert validate_feature_value_type(False) is True
        assert validate_feature_value_type("test") is True
        assert validate_feature_value_type(["a", "b", "c"]) is True
        assert validate_feature_value_type({"key": "value"}) is True
        assert validate_feature_value_type(FeatureValue("wrapped")) is True

    def test_validate_feature_value_type_rejects_invalid_types(self):
        assert validate_feature_value_type(123) is False
        assert validate_feature_value_type(12.34) is False
        assert validate_feature_value_type([1, 2, 3]) is False
        assert validate_feature_value_type(["string", 123]) is False
        assert validate_feature_value_type({1: "value"}) is False
        assert validate_feature_value_type({"key": 123}) is False
        assert validate_feature_value_type(None) is False
        assert validate_feature_value_type(object()) is False
        assert validate_feature_value_type(set()) is False

    def test_format_feature_value_for_display_accepts_raw_and_wrapped_values(self):
        assert format_feature_value_for_display(False) == "false"
        assert format_feature_value_for_display("mime") == "mime"
        assert format_feature_value_for_display(FeatureValue({"phase": ["entry", "exit"]})) == (
            "{'phase': ['entry', 'exit']}"
        )
