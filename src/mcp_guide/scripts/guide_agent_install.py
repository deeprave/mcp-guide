#!/usr/bin/env python3
"""Install agent configurations."""

import argparse
import shutil
import sys
from pathlib import Path


def get_available_agents() -> dict[str, Path]:
    """Get available agents by scanning for install.dir files."""
    agents_base = Path(__file__).parent.parent / "mcp_guide" / "agents"
    available: dict[str, Path] = {}

    if not agents_base.exists() or not agents_base.is_dir():
        return available

    for agent_dir in agents_base.iterdir():
        if agent_dir.is_dir():
            install_file = agent_dir / "install.dir"
            if install_file.exists():
                available[agent_dir.name] = agent_dir

    return available


def main() -> int:
    """Main entry point."""
    available_agents = get_available_agents()
    agents_base = Path(__file__).parent.parent / "mcp_guide" / "agents"

    parser = argparse.ArgumentParser(
        description="Install agent configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  guide-agent-install <agent> ~
  guide-agent-install <agent> . -f
  guide-agent-install <agent> /path/dir

Available agents: {", ".join(sorted(available_agents.keys()))}""",
    )

    parser.add_argument("agent", nargs="?", help="Agent to install")
    parser.add_argument("dirname", nargs="?", help="Target directory (supports ~ and . expansion)")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("-l", "--list", action="store_true", help="List available agents")

    args = parser.parse_args()

    # List agents
    if args.list:
        print("Available agents:")
        for agent_name in sorted(available_agents.keys()):
            print(f"  - {agent_name}")
        return 0

    # No agent - show main README
    if not args.agent:
        readme_path = agents_base / "README.md"
        if readme_path.exists():
            print(readme_path.read_text())
        else:
            parser.print_help()
        return 0

    # Invalid agent
    if args.agent not in available_agents:
        print(f"Error: Unknown agent '{args.agent}'", file=sys.stderr)
        print(f"Available agents: {', '.join(sorted(available_agents.keys()))}", file=sys.stderr)
        return 1

    # Agent specified but no directory - show agent README
    if not args.dirname:
        agent_readme = agents_base / args.agent / "README.md"
        if agent_readme.exists():
            print(agent_readme.read_text())
            return 0
        else:
            print(f"Error: No README found for agent '{args.agent}'", file=sys.stderr)
            return 1

    # Install agent
    dirname = Path(args.dirname).expanduser().resolve()
    agent_dir = available_agents[args.agent]
    install_dir_file = agent_dir / "install.dir"

    # Read and validate install paths
    install_paths = [p.strip() for p in install_dir_file.read_text().strip().split("\n") if p.strip()]

    if not install_paths:
        print(f"Error: {install_dir_file} is empty or malformed", file=sys.stderr)
        return 1

    # Validate paths are relative and safe
    for path in install_paths:
        if Path(path).is_absolute() or ".." in Path(path).parts:
            print(f"Error: Invalid path in {install_dir_file}: {path}", file=sys.stderr)
            print("Paths must be relative and not contain '..'", file=sys.stderr)
            return 1

    # Determine which path to use based on dirname
    home_dir = Path.home()
    if dirname == home_dir and len(install_paths) > 1:
        install_path = install_paths[1]  # Use second line for home directory
    else:
        install_path = install_paths[0]  # Use first line for project directories

    target_dir = dirname / install_path
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []

    # Read file pattern from install.pattern file
    pattern_file = agent_dir / "install.pattern"
    if pattern_file.exists():
        file_pattern = pattern_file.read_text().strip()
    else:
        # Fallback to *.json if no pattern file exists
        file_pattern = "*.json"

    for agent_file in agent_dir.glob(file_pattern):
        if agent_file.name in ("README.md", "install.dir", "install.pattern"):
            continue
        target_file = target_dir / agent_file.name
        if target_file.exists() and not args.force:
            skipped.append(agent_file.name)
        else:
            shutil.copy2(agent_file, target_dir)
            installed.append(agent_file.name)

    print(f"Installed {args.agent} agents to: {target_dir}")

    if installed:
        print("Installed agents:")
        for name in installed:
            print(f"  - {Path(name).stem}")

    if skipped:
        print("Skipped (already exist):")
        for name in skipped:
            print(f"  - {name} exists and will be left untouched")

    return 0


if __name__ == "__main__":
    sys.exit(main())
