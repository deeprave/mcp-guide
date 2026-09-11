"""Document cache policy parsing and composition."""

from dataclasses import dataclass
from enum import StrEnum
from functools import total_ordering
from typing import Any, Iterable


class CacheScope(StrEnum):
    """Visibility scope for a cacheable document response."""

    PUBLIC = "public"
    PRIVATE = "private"


_LIFETIME_TTLS_MS = {
    "long": 86_400_000,
    "medium": 900_000,
    "short": 120_000,
}
_SCOPE_RESTRICTIVENESS = {
    CacheScope.PUBLIC: 1,
    CacheScope.PRIVATE: 0,
}
_SCOPE_ALIASES = {"shared": CacheScope.PUBLIC}


@total_ordering
@dataclass(frozen=True, eq=False)
class CachePolicy:
    """A cache policy declared by document frontmatter.

    Policies sort from most restrictive to least restrictive.  Composition uses
    the smallest lifetime and most restrictive scope, while an absent policy
    disables caching for the combined document.
    """

    ttl_ms: int | None = None
    scope: CacheScope | None = None

    @classmethod
    def no_cache(cls) -> "CachePolicy":
        """Return the non-cacheable policy."""
        return cls()

    @classmethod
    def long_public(cls) -> "CachePolicy":
        """Return the default policy for static Markdown documents."""
        return cls(ttl_ms=_LIFETIME_TTLS_MS["long"], scope=CacheScope.PUBLIC)

    @classmethod
    def parse(cls, value: Any) -> tuple["CachePolicy", str | None]:
        """Parse a frontmatter cache value and report malformed declarations."""
        if value is None:
            return cls.no_cache(), None
        if not isinstance(value, str):
            return cls.no_cache(), f"Invalid cache policy: {value!r}"

        parts = [part.strip().lower() for part in value.split(",")]
        if not value.strip() or not all(parts):
            return cls.no_cache(), f"Invalid cache policy: {value!r}"
        if len(parts) > 2 or any(part in {"none", "no-cache"} for part in parts) and len(parts) != 1:
            return cls.no_cache(), f"Invalid cache policy: {value!r}"
        if parts[0] in {"none", "no-cache"}:
            return cls.no_cache(), None

        lifetime = next((part for part in parts if part in _LIFETIME_TTLS_MS), None)
        scope_name = next((part for part in parts if part in CacheScope or part in _SCOPE_ALIASES), None)
        if len(set(parts)) != len(parts) or len(parts) != sum(item is not None for item in (lifetime, scope_name)):
            return cls.no_cache(), f"Invalid cache policy: {value!r}"

        return cls(
            ttl_ms=_LIFETIME_TTLS_MS[lifetime] if lifetime else _LIFETIME_TTLS_MS["medium"],
            scope=(CacheScope(scope_name) if scope_name in CacheScope else _SCOPE_ALIASES[scope_name])
            if scope_name
            else CacheScope.PUBLIC,
        ), None

    @property
    def is_cacheable(self) -> bool:
        """Whether this policy permits caching."""
        return self.ttl_ms is not None and self.scope is not None

    @property
    def metadata(self) -> dict[str, int | str] | None:
        """Return the metadata representation for a cacheable policy."""
        ttl_ms = self.ttl_ms
        scope = self.scope
        if ttl_ms is None or scope is None:
            return None
        return {"ttl_ms": ttl_ms, "scope": scope.value}

    @classmethod
    def combine(cls, policies: Iterable["CachePolicy"]) -> "CachePolicy":
        """Combine document and rendered-partial policies conservatively."""
        policies = tuple(policies)
        if not policies or any(not policy.is_cacheable for policy in policies):
            return cls.no_cache()

        return cls(
            ttl_ms=min(policy.ttl_ms for policy in policies if policy.ttl_ms is not None),
            scope=min(
                (policy.scope for policy in policies if policy.scope is not None),
                key=lambda scope: _SCOPE_RESTRICTIVENESS[scope],
            ),
        )

    def __eq__(self, other: object) -> bool:
        """Compare policies by their declared cacheability."""
        if not isinstance(other, CachePolicy):
            return NotImplemented
        return (self.ttl_ms, self.scope) == (other.ttl_ms, other.scope)

    def __lt__(self, other: object) -> bool:
        """Order policies from most restrictive to least restrictive."""
        if not isinstance(other, CachePolicy):
            return NotImplemented
        return self._precedence_key() < other._precedence_key()

    def _precedence_key(self) -> tuple[int, int, int]:
        """Return the ordering key used by the rich comparison operators."""
        if not self.is_cacheable:
            return (0, 0, 0)
        assert self.scope is not None
        assert self.ttl_ms is not None
        return (1, _SCOPE_RESTRICTIVENESS[self.scope], self.ttl_ms)
