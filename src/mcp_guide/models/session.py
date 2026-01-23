"""Session state model."""

from dataclasses import dataclass, field


@dataclass
class SessionState:
    """Mutable runtime state for a session."""

    current_dir: str = ""
    cache: dict[str, object] = field(default_factory=dict)
