"""CLI argument parsing and configuration."""

import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import click


def parse_transport_mode(mode_str: str) -> tuple[str, Optional[str], Optional[int]]:
    """Parse transport mode string into mode, host, and port.

    Args:
        mode_str: Transport mode string (stdio, http, https, http://host:port, etc.)

    Returns:
        Tuple of (mode, host, port)

    Raises:
        ValueError: If mode string is invalid
    """
    # Handle simple modes
    if mode_str == "stdio":
        return ("stdio", None, None)

    if mode_str == "http":
        return ("http", "localhost", 8080)

    if mode_str == "https":
        return ("https", "0.0.0.0", 443)  # nosec B104 - intentional for HTTPS external access

    # Parse URL format
    if "://" in mode_str:
        try:
            parsed = urlparse(mode_str)
        except ValueError as e:
            raise ValueError(f"Invalid port: {e}")

        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid transport mode: {parsed.scheme}")

        # Determine host
        host = parsed.hostname
        if not host:
            # Empty host (e.g., http://:8080)
            host = "localhost" if parsed.scheme == "http" else "0.0.0.0"  # nosec B104 - intentional for HTTPS

        # Determine port
        port = parsed.port
        if port is None:
            port = 8080 if parsed.scheme == "http" else 443

        # Validate port
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid port: {port}")

        return (parsed.scheme, host, port)

    raise ValueError(
        f"Invalid transport mode: {mode_str}. Must be one of: stdio, http, https, or a URL like http://host:port"
    )


@dataclass
class ServerConfig:
    """MCP server configuration from CLI and environment variables."""

    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_json: bool = False
    tool_prefix: str = "guide"
    docroot: Optional[str] = None
    configdir: Optional[str] = None

    # Transport configuration
    transport_mode: str = "stdio"
    transport_host: Optional[str] = None
    transport_port: Optional[int] = None

    # Error tracking for deferred logging
    cli_error: Optional[click.ClickException] = None
    should_exit: bool = False


def parse_args() -> ServerConfig:
    """Parse command line arguments and return server configuration.

    Uses Click adapter pattern to parse args and return config dataclass
    instead of Click's normal run-and-exit behavior.

    Priority order for each setting:
    1. Command line argument (highest)
    2. Environment variable (via Click's envvar)
    3. Default value (lowest)

    Exception: --no-tool-prefix overrides all other prefix settings.

    Error Handling:
    - Help/version flags: Stored in config, exit after logging configured
    - Invalid arguments: Stored in config, logged, continue with defaults
    - Ctrl+C: Stored in config, exit with code 130

    Returns:
        ServerConfig with parsed configuration and any CLI errors

    Raises:
        None - all Click exceptions are caught and stored in config
    """
    config = ServerConfig()

    # Get version from package metadata
    try:
        from importlib.metadata import version

        pkg_version = version("mcp-guide")
    except Exception:
        pkg_version = "unknown"

    def _version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
        """Callback for version option."""
        if not value or ctx.resilient_parsing:
            return
        click.echo(f"mcp-guide, version {pkg_version}")
        # Mark that we should exit after printing
        config.should_exit = True

    @click.command(context_settings={"help_option_names": ["-h", "--help"]})
    @click.argument(
        "transport",
        type=str,
        default="stdio",
        required=False,
    )
    @click.option(
        "-V",
        "--version",
        is_flag=True,
        expose_value=False,
        is_eager=True,
        callback=_version_callback,
        help="Show the version and exit.",
    )
    @click.option(
        "--log-level",
        envvar="MG_LOG_LEVEL",
        type=click.Choice(["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
        default="INFO",
        help="Logging level (env: MG_LOG_LEVEL)",
    )
    @click.option(
        "--log-file",
        envvar="MG_LOG_FILE",
        type=click.Path(),
        help="Log file path (env: MG_LOG_FILE)",
    )
    @click.option(
        "--log-json",
        envvar="MG_LOG_JSON",
        is_flag=True,
        help="Enable JSON log format (env: MG_LOG_JSON)",
    )
    @click.option(
        "--tool-prefix",
        envvar="MCP_TOOL_PREFIX",
        type=str,
        help="Custom tool prefix (env: MCP_TOOL_PREFIX, default: guide)",
    )
    @click.option(
        "--no-tool-prefix",
        is_flag=True,
        help="Disable tool prefix",
    )
    @click.option(
        "-d",
        "--docroot",
        envvar="MG_DOCROOT",
        type=click.Path(),
        help="Custom docroot path (env: MG_DOCROOT)",
    )
    @click.option(
        "-c",
        "--configdir",
        envvar="MG_CONFIGDIR",
        type=click.Path(),
        help="Custom config directory (env: MG_CONFIGDIR)",
    )
    @click.pass_context
    def cli(
        ctx: click.Context,
        transport: str,
        log_level: str,
        log_file: Optional[str],
        log_json: bool,
        tool_prefix: Optional[str],
        no_tool_prefix: bool,
        docroot: Optional[str],
        configdir: Optional[str],
    ) -> None:
        """MCP Guide Server."""
        # Parse transport mode
        try:
            mode, host, port = parse_transport_mode(transport)
            config.transport_mode = mode
            config.transport_host = host
            config.transport_port = port
        except ValueError as e:
            raise click.UsageError(str(e))

        # Validate mutual exclusion using Click's context
        # Check if --tool-prefix was explicitly provided on command line (not from envvar)
        tool_prefix_source = ctx.get_parameter_source("tool_prefix")
        if no_tool_prefix and tool_prefix_source == click.core.ParameterSource.COMMANDLINE:
            raise click.UsageError("Cannot use both --tool-prefix and --no-tool-prefix")

        # Populate config
        config.log_level = log_level.upper()
        config.log_file = log_file
        config.log_json = log_json
        config.docroot = docroot
        config.configdir = configdir

        # Tool prefix priority: --no-tool-prefix > --tool-prefix > envvar > default
        if no_tool_prefix:
            config.tool_prefix = ""
        elif tool_prefix is not None:
            config.tool_prefix = tool_prefix
        # else: Click already set from envvar or we keep default "guide"

    # Parse args - help/version print but don't exit with standalone_mode=False
    try:
        cli(standalone_mode=False)

        # Check if help was requested (Click prints but doesn't exit with standalone_mode=False)
        if "-h" in sys.argv or "--help" in sys.argv:
            config.should_exit = True

    except click.exceptions.Exit as e:
        # Help/version/other exit paths - mark for exit
        config.should_exit = True
        # Exit code 0 means help/version, non-zero means error
        if e.exit_code != 0:
            config.cli_error = e  # type: ignore[assignment]
    except click.Abort as e:
        # Ctrl+C - store for deferred handling
        config.cli_error = e  # type: ignore[assignment]
        config.should_exit = True
    except click.ClickException as e:
        # UsageError, BadParameter, etc - store for deferred logging
        config.cli_error = e
        config.should_exit = False

    return config
