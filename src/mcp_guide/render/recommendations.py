"""Parsing and labelling for embedded Guide recommendations."""

import re
from dataclasses import dataclass
from hashlib import sha256

RECOMMENDATION_TYPES = frozenset({"skill", "command", "content", "tool"})
_LABEL_COMPONENT = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Recommendation:
    """A validated recommendation embedded in a rendered template."""

    kind: str
    name: str

    @property
    def label(self) -> str:
        """Return a deterministic, collision-resistant Markdown footnote label."""
        readable_name = _LABEL_COMPONENT.sub("-", self.name.lower()).strip("-") or "item"
        digest = sha256(f"{self.kind}:{self.name}".encode()).hexdigest()[:12]
        return f"guide-recommendation-{self.kind}-{readable_name}-{digest}"


def parse_recommendation(value: str) -> Recommendation:
    """Parse a typed recommendation, defaulting untyped values to content."""
    recommendation = value.strip()
    if not recommendation:
        raise ValueError("Recommendation must name a skill, command, content document, or tool")

    prefix, separator, name = recommendation.partition(":")
    if not separator:
        return Recommendation("content", recommendation)

    kind = prefix.strip()
    name = name.strip()
    if kind not in RECOMMENDATION_TYPES:
        raise ValueError(f"Unknown recommendation type: {kind or '<empty>'}")
    if not name:
        raise ValueError(f"Recommendation {kind!r} must name a target")
    return Recommendation(kind, name)
