"""Tests for command argument parser."""

from mcp_guide.prompts.command_parser import parse_command_arguments


class TestCommandArgumentParser:
    """Tests for parse_command_arguments function."""

    def test_parse_simple_flags(self):
        """Test parsing simple flags."""
        argv = [":help", "--verbose", "--dry-run"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"_verbose": True, "_dry_run": True}
        assert args == []
        assert errors == []

    def test_parse_negation_flags(self):
        """Test parsing --no-flag negation."""
        argv = [":command", "--no-verbose", "--no-dry-run"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"_verbose": False, "_dry_run": False}
        assert args == []
        assert errors == []

    def test_parse_flag_with_value(self):
        """Test parsing --key=value flags."""
        argv = [":command", "--type=docs", "--name=test-category"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"_type": "docs", "_name": "test-category"}
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

        assert kwargs == {"_dry_run": True, "_type": "docs", "description": "test"}
        assert args == ["my-collection", "category1"]
        assert errors == []

    def test_parse_errors_empty_flag(self):
        """Test error handling for empty flags."""
        argv = [":command", "--"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == ["Invalid flag: -- (empty flag name)"]

    def test_parse_errors_empty_value(self):
        """Test error handling for empty values."""
        argv = [":command", "--key="]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == ["Invalid flag: --key= (empty value)"]

    def test_parse_errors_empty_key(self):
        """Test error handling for empty keys."""
        argv = [":command", "=value"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == ["Invalid argument: starts with '=' but no key"]

    def test_parse_errors_malformed_flag(self):
        """Test error handling for malformed flags."""
        argv = [":command", "--=value"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {}
        assert args == []
        assert errors == ["Invalid flag: empty key before '='"]

    def test_hyphen_to_underscore_conversion(self):
        """Test that hyphens are converted to underscores in flag names."""
        argv = [":command", "--dry-run-mode", "--no-verbose-output"]
        kwargs, args, errors = parse_command_arguments(argv)

        assert kwargs == {"_dry_run_mode": True, "_verbose_output": False}
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

        assert kwargs == {"_v": True, "_f": True}
        assert args == []
        assert errors == []

    def test_parse_short_flag_with_mapping(self):
        """Test parsing short flags with explicit mapping."""
        argv = [":command", "-v", "-d", "-x"]
        short_flag_map = {"v": "verbose", "d": "dry_run", "x": "debug"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"_verbose": True, "_dry_run": True, "_debug": True}
        assert args == []
        assert errors == []

    def test_parse_short_flag_with_value_mapping(self):
        """Test parsing short flag with value and mapping."""
        argv = [":command", "-t=docs", "-n=test"]
        short_flag_map = {"t": "type", "n": "name"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"_type": "docs", "_name": "test"}
        assert args == []
        assert errors == []

    def test_parse_combined_short_flags_with_mapping(self):
        """Test parsing combined short flags with mapping."""
        argv = [":command", "-vdf"]
        short_flag_map = {"v": "verbose", "d": "dry_run", "f": "force"}
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"_verbose": True, "_dry_run": True, "_force": True}
        assert args == []
        assert errors == []

    def test_parse_mixed_mapping_and_fallback(self):
        """Test that unmapped short flags fall back to themselves."""
        argv = [":command", "-v", "-x", "-f"]
        short_flag_map = {"v": "verbose", "f": "force"}  # x not mapped
        kwargs, args, errors = parse_command_arguments(argv, short_flag_map)

        assert kwargs == {"_verbose": True, "_x": True, "_force": True}
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

        assert kwargs == {"_v": True, "_f": True}  # Valid chars still processed
        assert args == []
        assert errors == ["Invalid flag character: -@"]
