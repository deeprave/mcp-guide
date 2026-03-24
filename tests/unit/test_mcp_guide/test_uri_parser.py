"""Tests for guide:// URI parser."""

import pytest

from mcp_guide.uri_parser import GuideUri, parse_guide_uri

COMMANDS = ["project", "status", "help", "openspec/list", "openspec/show", "perm/write-add", "perm/read-add"]


class TestContentUri:
    """Content URI parsing tests."""

    def test_expression_only(self) -> None:
        result = parse_guide_uri("guide://docs")
        assert result == GuideUri(is_command=False, expression="docs")

    def test_expression_with_pattern(self) -> None:
        result = parse_guide_uri("guide://docs/readme")
        assert result == GuideUri(is_command=False, expression="docs", pattern="readme")

    def test_expression_with_deep_pattern(self) -> None:
        result = parse_guide_uri("guide://lang/python/style")
        assert result == GuideUri(is_command=False, expression="lang", pattern="python/style")

    def test_trailing_slash_stripped_from_pattern(self) -> None:
        result = parse_guide_uri("guide://docs/readme/")
        assert result == GuideUri(is_command=False, expression="docs", pattern="readme")

    def test_trailing_slash_only_pattern_becomes_none(self) -> None:
        result = parse_guide_uri("guide://docs/")
        assert result == GuideUri(is_command=False, expression="docs", pattern=None)


class TestCommandUri:
    """Command URI parsing tests."""

    def test_simple_command(self) -> None:
        result = parse_guide_uri("guide://_project", COMMANDS)
        assert result == GuideUri(is_command=True, expression="project")

    def test_command_path_property(self) -> None:
        result = parse_guide_uri("guide://_project", COMMANDS)
        assert result.command_path == "project"

    def test_command_path_none_for_content(self) -> None:
        result = parse_guide_uri("guide://docs")
        assert result.command_path is None

    def test_command_with_args(self) -> None:
        result = parse_guide_uri("guide://_perm/write-add/docs/", COMMANDS)
        assert result == GuideUri(is_command=True, expression="perm/write-add", args=["docs"])

    def test_command_with_kwargs(self) -> None:
        result = parse_guide_uri("guide://_status?verbose=true", COMMANDS)
        assert result == GuideUri(is_command=True, expression="status", kwargs={"verbose": True})

    def test_command_with_args_and_kwargs(self) -> None:
        result = parse_guide_uri("guide://_openspec/list?verbose=true", COMMANDS)
        assert result == GuideUri(is_command=True, expression="openspec/list", kwargs={"verbose": True})

    def test_longest_match_resolution(self) -> None:
        result = parse_guide_uri("guide://_openspec/show/my-change", COMMANDS)
        assert result == GuideUri(is_command=True, expression="openspec/show", args=["my-change"])

    def test_no_match_uses_first_segment(self) -> None:
        result = parse_guide_uri("guide://_unknown/arg1", COMMANDS)
        assert result == GuideUri(is_command=True, expression="unknown", args=["arg1"])

    def test_empty_command_names_raises(self) -> None:
        with pytest.raises(ValueError, match="Command not found"):
            parse_guide_uri("guide://_foo/bar", [])

    def test_no_command_names_raises(self) -> None:
        """First parse (without command_names) detects command URI without resolving."""
        result = parse_guide_uri("guide://_foo")
        assert result.is_command is True
        assert result.expression == "foo"


class TestQueryParams:
    """Query parameter parsing tests."""

    def test_boolean_flag_without_value(self) -> None:
        result = parse_guide_uri("guide://_status?verbose", COMMANDS)
        assert result.kwargs == {"verbose": True}

    def test_boolean_true(self) -> None:
        result = parse_guide_uri("guide://_status?verbose=true", COMMANDS)
        assert result.kwargs == {"verbose": True}

    def test_boolean_false(self) -> None:
        result = parse_guide_uri("guide://_status?verbose=false", COMMANDS)
        assert result.kwargs == {"verbose": False}

    def test_string_value(self) -> None:
        result = parse_guide_uri("guide://_openspec/show?change=my-feature", COMMANDS)
        assert result.kwargs == {"change": "my-feature"}

    def test_multiple_params(self) -> None:
        result = parse_guide_uri("guide://_openspec/show?change=my-feature&verbose=true", COMMANDS)
        assert result.kwargs == {"change": "my-feature", "verbose": True}

    def test_duplicate_param_raises(self) -> None:
        with pytest.raises(ValueError, match="Multiple values for query parameter"):
            parse_guide_uri("guide://_status?verbose=true&verbose=false", COMMANDS)

    def test_empty_param_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Empty query parameter key"):
            parse_guide_uri("guide://_status?=value", COMMANDS)


class TestValidation:
    """URI validation tests."""

    def test_invalid_scheme(self) -> None:
        with pytest.raises(ValueError, match="Only guide://"):
            parse_guide_uri("http://docs")

    def test_empty_uri(self) -> None:
        with pytest.raises(ValueError, match="Empty guide://"):
            parse_guide_uri("guide://")

    def test_empty_command_path(self) -> None:
        with pytest.raises(ValueError, match="Empty command path"):
            parse_guide_uri("guide://_")

    def test_empty_netloc_raises(self) -> None:
        with pytest.raises(ValueError, match="missing category or collection"):
            parse_guide_uri("guide:///foo/bar")
