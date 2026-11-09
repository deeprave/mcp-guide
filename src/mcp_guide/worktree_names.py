"""Guide-issued readable labels for linked worktrees."""

import secrets
from collections.abc import Collection

_ADJECTIVES = (
    "brisk",
    "calm",
    "clever",
    "daring",
    "eager",
    "gentle",
    "languid",
    "ludicrous",
    "nimble",
    "steady",
)
_NOUNS = (
    "badger",
    "falcon",
    "lizard",
    "otter",
    "panda",
    "quokka",
    "raven",
    "tiger",
    "walrus",
    "wombat",
    "antelope",
    "beaver",
    "cassowary",
    "dolphin",
    "echidna",
    "gecko",
    "heron",
    "ibis",
    "jaguar",
    "koala",
)


def allocate_worktree_name(used_names: Collection[str] = ()) -> str:
    """Return a readable label that is absent from the supplied names."""
    used = set(used_names)
    candidates = [f"{adjective}-{noun}" for adjective in _ADJECTIVES for noun in _NOUNS]
    available = [candidate for candidate in candidates if candidate not in used]
    if available:
        return secrets.choice(available)
    return f"worktree-{secrets.token_hex(4)}"
