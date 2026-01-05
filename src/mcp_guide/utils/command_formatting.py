"""Command formatting utilities."""


def format_args_string(args_list: list[str]) -> str:
    """Convert args list to space-separated string with quotes for whitespace."""
    formatted_args = []
    for arg in args_list:
        if any(c.isspace() for c in arg):
            # Escape existing quotes and wrap in quotes
            escaped_arg = arg.replace('"', '\\"')
            formatted_args.append(f'"{escaped_arg}"')
        else:
            formatted_args.append(arg)
    return " ".join(formatted_args)
