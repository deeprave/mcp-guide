"""Command argument parser for guide prompt system."""

from typing import TypedDict


class ParsedCommand(TypedDict):
    """Parsed command result structure."""

    kwargs: dict[str, str | bool | int]
    args: list[str]
    errors: list[str]


def parse_command_arguments(
    argv: list[str], short_flag_map: dict[str, str] | None = None
) -> tuple[dict[str, str | bool | int], list[str], list[str]]:
    """Parse command arguments into kwargs, args, and parse_errors.

    Args:
        argv: List of arguments starting with command (e.g., [":help", "--verbose", "arg1"])
        short_flag_map: Optional mapping of short flags to long flags.
                       When provided, allows commands to support short flags like -v for --verbose.
                       Example: {"v": "verbose", "d": "dry_run"} would map -v to --verbose

    Returns:
        Tuple of (kwargs, args, parse_errors)
        - kwargs: Dict with flag/key-value pairs (flags have underscore prefix)
        - args: List of positional arguments
        - errors: List of parsing error messages
    """
    kwargs: dict[str, str | bool | int] = {}
    args: list[str] = []
    parse_errors: list[str] = []

    if short_flag_map is None:
        short_flag_map = {}

    # Auto-generate short mappings for long flags found in argv, but don't overwrite explicit mappings
    for arg in argv[1:]:
        if arg.startswith("--") and "=" in arg:
            flag_name = arg[2:].split("=")[0]  # Extract flag name before =
            if flag_name and not flag_name.startswith("no-"):
                short_char = flag_name[0]
                if short_char not in short_flag_map:
                    short_flag_map[short_char] = flag_name
        elif arg.startswith("--") and len(arg) > 2:
            flag_name = arg[2:]
            if flag_name and not flag_name.startswith("no-"):
                short_char = flag_name[0]
                if short_char not in short_flag_map:
                    short_flag_map[short_char] = flag_name

    def resolve_short_flag(short_flag: str) -> str:
        """Resolve short flag to long form, with fallback to the short flag itself."""
        return short_flag_map.get(short_flag, short_flag)

    # Skip the command itself (first argument)
    for arg in argv[1:]:
        if arg.startswith("--"):
            # Handle --flag, --no-flag, --key=value
            if "=" in arg:
                # --key=value format
                key_part, value_part = arg[2:].split("=", 1)
                if not key_part:
                    parse_errors.append("Invalid flag: empty key before '='")
                    continue
                if not value_part:
                    parse_errors.append(f"Invalid flag: --{key_part}= (empty value)")
                    continue
                # Convert hyphens to underscores and add underscore prefix for flags
                key = "_" + key_part.replace("-", "_")
                kwargs[key] = value_part
            else:
                # --flag or --no-flag format
                flag_name = arg[2:]  # Remove --
                if not flag_name:
                    parse_errors.append("Invalid flag: -- (empty flag name)")
                    continue

                if flag_name.startswith("no-") and len(flag_name) > 3:
                    # --no-flag format (negation)
                    actual_flag = flag_name[3:]  # Remove "no-"
                    key = "_" + actual_flag.replace("-", "_")
                    kwargs[key] = False
                else:
                    # --flag format
                    key = "_" + flag_name.replace("-", "_")
                    kwargs[key] = True
        elif arg.startswith("-") and len(arg) > 1 and not arg.startswith("--"):
            # Handle single-dash short flags like -v, -f, -abc (combined)
            flags = arg[1:]  # Remove -
            if "=" in flags:
                # -k=value format
                key_part, value_part = flags.split("=", 1)
                if not key_part:
                    parse_errors.append("Invalid flag: empty key before '='")
                    continue
                if not value_part:
                    parse_errors.append(f"Invalid flag: -{key_part}= (empty value)")
                    continue
                # Single letter flag with value - resolve through mapping
                long_form = resolve_short_flag(key_part)
                key = "_" + long_form
                kwargs[key] = value_part
            else:
                # -v or -abc (combined flags)
                for flag_char in flags:
                    if not flag_char.isalnum():
                        parse_errors.append(f"Invalid flag character: -{flag_char}")
                        continue
                    # Resolve short flag to long form
                    long_form = resolve_short_flag(flag_char)
                    key = "_" + long_form
                    kwargs[key] = True
        elif "=" in arg and not arg.startswith("="):
            # Handle key=value format (no dashes)
            key_part, value_part = arg.split("=", 1)
            if not key_part:
                parse_errors.append("Invalid argument: empty key before '='")
                continue
            # No underscore prefix for key=value pairs
            kwargs[key_part] = value_part
        else:
            # Positional argument
            if arg.startswith("="):
                parse_errors.append("Invalid argument: starts with '=' but no key")
                continue
            args.append(arg)

    return kwargs, args, parse_errors
