"""Tests for command argument parser."""

import pytest

from mcp_guide.prompts.command_parser import parse_command_arguments


class TestCommandArgumentParser:
    """Tests for parse_command_arguments function."""

    def test_parse_simple_flags(self):
        """Test parsing simple flags."""
        argv = [":help", "--verbose", "--dry-run"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"verbose": True, "dry_run": True}
        assert args == []
        assert errors == []

    def test_parse_negation_flags(self):
        """Test parsing --no-flag negation."""
        argv = [":command", "--no-verbose", "--no-dry-run"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"verbose": False, "dry_run": False}
        assert args == []
        assert errors == []

    def test_parse_flag_with_value(self):
        """Test parsing --key=value flags."""
        argv = [":command", "--type=docs", "--name=test-category"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"type": "docs", "name": "test-category"}
        assert args == []
        assert errors == []

    def test_parse_key_value_pairs(self):
        """Test parsing key=value pairs without dashes."""
        argv = [":command", "description=test desc", "setting=config"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"description": "test desc", "setting": "config"}
        assert args == []
        assert errors == []

    def test_parse_positional_args(self):
        """Test parsing positional arguments."""
        argv = [":command", "arg1", "arg2", "arg with spaces"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == ["arg1", "arg2", "arg with spaces"]
        assert errors == []

    def test_parse_mixed_arguments(self):
        """Test parsing mixed argument types."""
        argv = [":create/collection", "--dry-run", "--type=docs", "description=test", "my-collection", "category1"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"dry_run": True, "type": "docs", "description": "test"}
        assert args == ["my-collection", "category1"]
        assert errors == []

    @pytest.mark.parametrize(
        "argv,expected_error",
        [
            (["--"], "Invalid flag: -- (empty flag name)"),
            (["--key="], "Invalid flag: --key= (empty value)"),
            (["=value"], "Invalid argument: starts with '=' but no key"),
            (["--=value"], "Invalid flag: empty key before '='"),
        ],
        ids=["empty_flag", "empty_value", "empty_key", "malformed_flag"],
    )
    def test_parse_errors(self, argv, expected_error):
        """Test error handling for various invalid argument formats."""
        argv = [":command"] + argv
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == [expected_error]

    def test_hyphen_to_underscore_conversion(self):
        """Test that hyphens are converted to underscores in flag names."""
        argv = [":command", "--dry-run-mode", "--no-verbose-output"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"dry_run_mode": True, "verbose_output": False}
        assert args == []
        assert errors == []

    def test_empty_command_args(self):
        """Test parsing command with no arguments."""
        argv = [":help"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == []

    def test_parse_short_flags(self):
        """Test parsing single-letter flags like -v, -f."""
        argv = [":command", "-v", "-f"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"verbose": True, "force": True}
        assert args == []
        assert errors == []

    def test_parse_short_flag_with_mapping(self):
        """Test parsing short flags with explicit mapping."""
        argv = [":command", "-v", "-d", "-x"]
        short_flag_map = {"v": "verbose", "d": "dry_run", "x": "debug"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"verbose": True, "dry_run": True, "debug": True}
        assert args == []
        assert errors == []

    def test_parse_short_flag_with_value_mapping(self):
        """Test parsing short flag with value and mapping."""
        argv = [":command", "-t=docs", "-n=test"]
        short_flag_map = {"t": "type", "n": "name"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"type": "docs", "name": "test"}
        assert args == []
        assert errors == []

    def test_parse_combined_short_flags_with_mapping(self):
        """Test parsing combined short flags with mapping."""
        argv = [":command", "-vdf"]
        short_flag_map = {"v": "verbose", "d": "dry_run", "f": "force"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"verbose": True, "dry_run": True, "force": True}
        assert args == []
        assert errors == []

    def test_parse_mixed_mapping_and_fallback(self):
        """Test that unmapped short flags fall back to themselves."""
        argv = [":command", "-v", "-x", "-f"]
        short_flag_map = {"v": "verbose", "f": "force"}  # x not mapped
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"verbose": True, "x": True, "force": True}
        assert args == []
        assert errors == []

    def test_parse_short_flag_errors(self):
        """Test error handling for invalid short flags."""
        argv = [":command", "-=value", "-k="]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == ["Invalid flag: empty key before '='", "Invalid flag: -k= (empty value)"]

    def test_parse_invalid_short_flag_characters(self):
        """Test error handling for invalid characters in short flags."""
        argv = [":command", "-v@f"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"verbose": True, "force": True}  # Valid chars still processed
        assert args == []
        assert errors == ["Invalid flag character: -@"]


class TestArgRequiredFeature:
    """Tests for argrequired parameter - space-separated flag values."""

    def test_argrequired_with_space_syntax(self):
        """Test --flag value syntax when flag is in argrequired list."""
        argv = [":command", "--tracking", "GUIDE-177", "--verbose"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["tracking"])

        assert kwargs == {"tracking": "GUIDE-177", "verbose": True}
        assert args == []
        assert errors == []

    def test_argrequired_with_equals_syntax_still_works(self):
        """Test --flag=value syntax still works with argrequired."""
        argv = [":command", "--tracking=GUIDE-177", "--verbose"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["tracking"])

        assert kwargs == {"tracking": "GUIDE-177", "verbose": True}
        assert args == []
        assert errors == []

    def test_argrequired_missing_value_error(self):
        """Test error when required flag has no value."""
        argv = [":command", "--tracking"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["tracking"])

        assert kwargs == {}
        assert args == []
        assert errors == ["Flag --tracking requires a value"]

    def test_argrequired_next_token_is_flag_error(self):
        """Test error when required flag followed by another flag."""
        argv = [":command", "--tracking", "--verbose"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["tracking"])

        assert kwargs == {"verbose": True}
        assert args == []
        assert errors == ["Flag --tracking requires a value, got flag --verbose"]

    def test_argrequired_rejects_dash_prefixed_values(self):
        """Test that dash-prefixed values require equals syntax."""
        argv = [":command", "--threshold", "-5"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["threshold"])

        # -5 is parsed as short flag, threshold gets error
        assert "5" in kwargs  # -5 parsed as short flag
        assert errors == ["Flag --threshold requires a value, got flag -5"]

    def test_argrequired_accepts_quoted_negative_values(self):
        """Test that quoted negative values work (shell removes quotes)."""
        # Shell would pass this as: [":command", "--threshold", "-5"]
        # But with equals syntax, it works:
        argv = [":command", "--threshold=-5"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["threshold"])

        assert kwargs == {"threshold": "-5"}
        assert args == []
        assert errors == []

    def test_argrequired_multiple_flags(self):
        """Test multiple flags in argrequired list."""
        argv = [":command", "--issue", "feature-123", "--description", "Test feature", "--verbose"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["issue", "description"])

        assert kwargs == {"issue": "feature-123", "description": "Test feature", "verbose": True}
        assert args == []
        assert errors == []

    def test_argrequired_mixed_with_positional_args(self):
        """Test argrequired flags mixed with positional arguments."""
        argv = [":command", "--dir", "src/tests", "arg1", "--patterns", "*.py", "arg2"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=["dir", "patterns"])

        assert kwargs == {"dir": "src/tests", "patterns": "*.py"}
        assert args == ["arg1", "arg2"]
        assert errors == []

    def test_argrequired_none_preserves_current_behavior(self):
        """Test that argrequired=None preserves current boolean flag behavior."""
        argv = [":command", "--verbose", "arg1"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=None)

        assert kwargs == {"verbose": True}
        assert args == ["arg1"]
        assert errors == []

    def test_argrequired_empty_list_preserves_current_behavior(self):
        """Test that argrequired=[] preserves current boolean flag behavior."""
        argv = [":command", "--verbose", "arg1"]
        kwargs, args, errors = parse_command_arguments(argv, argrequired=[])

        assert kwargs == {"verbose": True}
        assert args == ["arg1"]
        assert errors == []
