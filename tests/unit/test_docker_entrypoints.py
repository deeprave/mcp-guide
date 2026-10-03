"""Container entrypoints deliver caller options to the real Guide CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def launcher_environment(tmp_path):
    """Parse launch options without starting a persistent MCP server."""
    launcher = tmp_path / "mcp-guide"
    launcher.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "from dataclasses import asdict\n"
        "from mcp_guide.cli import parse_args\n"
        "config = parse_args()\n"
        "if config.cli_error is not None:\n"
        "    raise config.cli_error\n"
        "print(json.dumps(asdict(config)))\n"
    )
    launcher.chmod(0o755)
    return {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
        "MG_LOG_LEVEL": "INFO",
        "MG_LOG_JSON": "0",
    }


def launch_entrypoint(name, args, env):
    script = Path(__file__).resolve().parents[2] / "docker" / f"entrypoint-{name}.sh"
    result = subprocess.run(["sh", str(script), *args], env=env, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize("name,mode", [("stdio", "stdio"), ("http-nossl", "http"), ("https", "https")])
def test_entrypoint_forwards_cli_options(name, mode, launcher_environment, tmp_path):
    """Dropping caller arguments would lose their log and configuration overrides."""
    configdir = tmp_path / "configuration with spaces"
    configdir.mkdir()
    config = launch_entrypoint(name, ["--log-level", "DEBUG", "--configdir", str(configdir)], launcher_environment)
    assert config["transport_mode"] == mode
    assert config["log_level"] == "DEBUG"
    assert config["configdir"] == str(configdir)


@pytest.mark.parametrize(
    "name,url,mode,host,port",
    [
        ("http-nossl", "http://127.0.0.1:9090/custom", "http", "127.0.0.1", 9090),
        ("https", "https://127.0.0.1:9443/custom", "https", "127.0.0.1", 9443),
    ],
)
def test_entrypoint_preserves_explicit_transport_url(name, url, mode, host, port, launcher_environment):
    """The transport URL supplies caller-selected binding and routing."""
    config = launch_entrypoint(name, [url], launcher_environment)
    assert config["transport_mode"] == mode
    assert config["transport_host"] == host
    assert config["transport_port"] == port
    assert config["transport_path"] == "custom"


@pytest.mark.parametrize("name", ["stdio", "http-nossl", "https"])
def test_entrypoint_uses_cli_logging_environment(name, launcher_environment):
    """Legacy LOG_* values must not override the public MG_* settings."""
    config = launch_entrypoint(
        name,
        [],
        {**launcher_environment, "MG_LOG_LEVEL": "DEBUG", "LOG_LEVEL": "ERROR", "LOG_JSON": "true"},
    )
    assert config["log_level"] == "DEBUG"
    assert config["log_json"] is False


def test_https_entrypoint_preserves_explicit_certificate_flags(launcher_environment, tmp_path):
    """Caller certificate paths reach Click's validation without being discarded."""
    cert = tmp_path / "custom cert.pem"
    key = tmp_path / "custom key.pem"
    cert.touch()
    key.touch()
    config = launch_entrypoint("https", ["--ssl-certfile", str(cert), "--ssl-keyfile", str(key)], launcher_environment)
    assert config["ssl_certfile"] == str(cert)
    assert config["ssl_keyfile"] == str(key)
