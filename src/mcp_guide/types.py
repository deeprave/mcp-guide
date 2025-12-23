"""Common type definitions for the MCP Guide project.

This module contains shared type aliases and type definitions used across
multiple modules in the MCP Guide project.

Type Aliases:
    YamlValue: Represents all possible YAML front matter values including
               nested structures. Used for parsing command metadata and
               template front matter.
"""

from typing import Union

# Type alias for YAML front matter values
# Supports all YAML data types including recursive structures
YamlValue = Union[str, int, float, bool, list["YamlValue"], dict[str, "YamlValue"], None]
