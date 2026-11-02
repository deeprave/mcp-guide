"""Shared command-option normalisation."""

from collections.abc import Mapping
from typing import Final

COMMON_SHORT_OPTION_ALIASES: Final = {
    "v": "verbose",
    "h": "help",
    "q": "quiet",
    "f": "force",
    "d": "debug",
    "t": "table",
}


def normalise_command_option_name(name: str, aliases: Mapping[str, str] | None = None) -> str:
    """Return a canonical command-option name, including known short aliases."""
    normalised_name = name.replace("-", "_")
    if aliases is not None and normalised_name in aliases:
        return aliases[normalised_name].replace("-", "_")
    return COMMON_SHORT_OPTION_ALIASES.get(normalised_name, normalised_name)
