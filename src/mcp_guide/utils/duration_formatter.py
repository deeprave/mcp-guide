"""Duration formatting utilities."""

from typing import Union


def format_duration(seconds: Union[int, float]) -> str:
    """Format seconds into [[Xh][Ym]]Z.zs format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string like "7h50m28.9s", "4m32.5s", or "27.5s"
    """
    result = ""

    # Add hours if >= 1 hour
    if seconds >= 3600:
        result += f"{int(seconds // 3600)}h"

    # Add minutes if >= 1 minute
    if seconds >= 60:
        result += f"{int((seconds % 3600) // 60)}m"

    # Always add seconds
    result += f"{seconds % 60:.1f}s"

    return result
