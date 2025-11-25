"""Main entry point for mcp-guide CLI."""

import click


@click.group()
@click.version_option(version="0.5.0", prog_name="mcp-guide")
def cli() -> None:
    """MCP Guide - Guidelines and project rules management."""
    pass


def cli_main() -> None:
    """Entry point for console script."""
    cli()


if __name__ == "__main__":
    cli_main()
