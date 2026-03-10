"""Tests for path flag validation and normalisation."""

import pytest

from mcp_guide.feature_flags.constants import FLAG_PATH_DOCUMENTS, FLAG_PATH_EXPORT
from mcp_guide.feature_flags.validators import (
    FlagValidationError,
    normalise_flag,
    normalise_path_flag,
    register_flag_validator,
    validate_flag_with_registered,
    validate_path_flag,
)


@pytest.fixture(autouse=True)
def _ensure_path_flags_registered():
    """Ensure path flag validators are registered (other tests may clear them)."""
    register_flag_validator(FLAG_PATH_DOCUMENTS, validate_path_flag, normaliser=normalise_path_flag)
    register_flag_validator(FLAG_PATH_EXPORT, validate_path_flag, normaliser=normalise_path_flag)


class TestValidatePathFlag:
    @pytest.mark.parametrize("path", [".todo/", ".todo", ".kiro/knowledge/"])
    def test_valid_paths(self, path):
        assert validate_path_flag(path, False) is True

    @pytest.mark.parametrize("path", ["", None, True, 42, "../etc/", "foo/../../bar"])
    def test_invalid_paths(self, path):
        assert validate_path_flag(path, False) is False


class TestNormalisePathFlag:
    @pytest.mark.parametrize(
        "input_val,expected",
        [
            (".todo", ".todo/"),
            (".todo/", ".todo/"),
            (True, True),
        ],
    )
    def test_normalise(self, input_val, expected):
        assert normalise_path_flag(input_val) == expected


class TestNormaliseFlag:
    @pytest.mark.parametrize(
        "flag,input_val,expected",
        [
            (FLAG_PATH_DOCUMENTS, ".todo", ".todo/"),
            (FLAG_PATH_EXPORT, ".knowledge", ".knowledge/"),
            ("unknown-flag", "value", "value"),
        ],
    )
    def test_normalise_flag(self, flag, input_val, expected):
        assert normalise_flag(flag, input_val) == expected


class TestPathFlagRegistration:
    @pytest.mark.parametrize(
        "flag,value",
        [
            (FLAG_PATH_DOCUMENTS, ".todo/"),
            (FLAG_PATH_EXPORT, ".knowledge/"),
        ],
    )
    def test_valid(self, flag, value):
        validate_flag_with_registered(flag, value, is_project=True)

    @pytest.mark.parametrize(
        "flag,value",
        [
            (FLAG_PATH_DOCUMENTS, True),
            (FLAG_PATH_EXPORT, "../secret/"),
        ],
    )
    def test_invalid(self, flag, value):
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(flag, value, is_project=True)

    def test_none_skips_validation(self):
        validate_flag_with_registered(FLAG_PATH_DOCUMENTS, None, is_project=True)
