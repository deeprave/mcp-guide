"""Tests for feature flag type system."""

from typing import get_args

from mcp_guide.feature_flags.types import FeatureValue, validate_feature_value_type


class TestFeatureValueType:
    """Test FeatureValue type alias and validation."""

    def test_feature_value_type_definition(self):
        """Test that FeatureValue includes correct types."""
        # Get the union args from FeatureValue
        args = get_args(FeatureValue)

        # Check that all expected base types are present
        assert bool in args
        assert str in args
        # Note: list[str] and dict[str, str] are generic aliases,
        # so we check for list and dict base types
        assert any(hasattr(arg, "__origin__") and arg.__origin__ is list for arg in args)
        assert any(hasattr(arg, "__origin__") and arg.__origin__ is dict for arg in args)

    def test_validate_feature_value_type_accepts_valid_types(self):
        """Test that validation accepts valid FeatureValue types."""
        # Boolean values
        assert validate_feature_value_type(True) is True
        assert validate_feature_value_type(False) is True

        # String values
        assert validate_feature_value_type("test") is True
        assert validate_feature_value_type("") is True

        # List of strings
        assert validate_feature_value_type(["a", "b", "c"]) is True
        assert validate_feature_value_type([]) is True
        assert validate_feature_value_type(["single"]) is True

        # Dict of string to string
        assert validate_feature_value_type({"key": "value"}) is True
        assert validate_feature_value_type({}) is True
        assert validate_feature_value_type({"k1": "v1", "k2": "v2"}) is True

    def test_validate_feature_value_type_rejects_invalid_types(self):
        """Test that validation rejects invalid types."""
        # Numeric types
        assert validate_feature_value_type(123) is False
        assert validate_feature_value_type(12.34) is False

        # Mixed lists
        assert validate_feature_value_type([1, 2, 3]) is False
        assert validate_feature_value_type(["string", 123]) is False
        assert validate_feature_value_type([True, False]) is False

        # Invalid dict types
        assert validate_feature_value_type({1: "value"}) is False
        assert validate_feature_value_type({"key": 123}) is False
        assert validate_feature_value_type({1: 2}) is False

        # Other types
        assert validate_feature_value_type(None) is False
        assert validate_feature_value_type(object()) is False
        assert validate_feature_value_type(set()) is False
