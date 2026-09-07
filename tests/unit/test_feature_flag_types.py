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

    def test_supported_shapes_validate_and_round_trip_through_the_wrapper(self):
        # Canonical shape coverage; validators.validate_flag_value is only an alias.
        values = [
            True,
            False,
            "",
            "multi word",
            [],
            ["", "value"],
            {},
            {"": ""},
            {"key": ["entry"]},
            FeatureValue("wrapped"),
        ]
        for value in values:
            assert validate_feature_value_type(value), value
            assert FeatureValue(value).to_raw() == to_raw_feature_value(value)

    def test_unsupported_shapes_are_rejected_by_validation_and_construction(self):
        values = [
            123,
            12.34,
            [1, 2],
            ["string", True],
            {1: "value"},
            {"key": 123},
            {"key": True},
            None,
            object(),
            set(),
            tuple(),
        ]
        for value in values:
            assert not validate_feature_value_type(value), value
            with pytest.raises(TypeError):
                FeatureValue(value)

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

    def test_format_feature_value_for_display_accepts_raw_and_wrapped_values(self):
        assert format_feature_value_for_display(False) == "false"
        assert format_feature_value_for_display("mime") == "mime"
        assert format_feature_value_for_display(FeatureValue({"phase": ["entry", "exit"]})) == (
            "{'phase': ['entry', 'exit']}"
        )
