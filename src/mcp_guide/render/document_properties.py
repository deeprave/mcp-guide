"""Typed frontmatter properties that compose across document contributors."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Self, TypeVar

from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.result_constants import AGENT_INFO, AGENT_INSTRUCTION, USER_INFO

_DocumentPropertyT = TypeVar("_DocumentPropertyT", bound="DocumentProperty")


class DocumentProperty:
    """A typed, composable frontmatter property."""

    @classmethod
    def handles_frontmatter_key(cls, key: str) -> bool:
        """Return whether this property consumes a frontmatter key."""
        raise NotImplementedError

    def apply_frontmatter(self, key: str, value: Any) -> None:
        """Apply a handled frontmatter value."""
        raise NotImplementedError

    @classmethod
    def combine(cls, properties: Iterable[Self]) -> Self:
        """Combine matching contributor properties."""
        raise NotImplementedError


@dataclass
class DocumentCache(DocumentProperty):
    """Cache behaviour derived from a document's ``cache`` frontmatter."""

    default: CachePolicy = field(default_factory=CachePolicy.no_cache)
    value: CachePolicy = field(init=False)
    diagnostic: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.value = self.default

    @classmethod
    def handles_frontmatter_key(cls, key: str) -> bool:
        return key == "cache"

    def apply_frontmatter(self, key: str, value: Any) -> None:
        self.value, self.diagnostic = CachePolicy.parse_with_diagnostic(value)

    @classmethod
    def combine(cls, properties: Iterable[Self]) -> Self:
        return cls(default=CachePolicy.combine(property.value for property in properties))


_TYPE_PRECEDENCE = {
    USER_INFO: 0,
    AGENT_INFO: 1,
    AGENT_INSTRUCTION: 2,
}
_PRECEDENCE_TO_TYPE = {value: key for key, value in _TYPE_PRECEDENCE.items()}


@dataclass
class DocumentDisposition(DocumentProperty):
    """Delivery disposition derived from a document's ``type`` frontmatter."""

    default: str | None = USER_INFO
    value: str | None = field(init=False)

    def __post_init__(self) -> None:
        self.value = self.default

    @classmethod
    def handles_frontmatter_key(cls, key: str) -> bool:
        return key == "type"

    def apply_frontmatter(self, key: str, value: Any) -> None:
        self.value = value if isinstance(value, str) and value in _TYPE_PRECEDENCE else None

    @classmethod
    def combine(cls, properties: Iterable[Self]) -> Self:
        values = [property.value for property in properties if property.value in _TYPE_PRECEDENCE]
        if not values:
            return cls(default=None)
        precedence = max(_TYPE_PRECEDENCE[value] for value in values)
        return cls(default=_PRECEDENCE_TO_TYPE[precedence])


@dataclass
class DocumentProperties:
    """Collection of typed properties derived from a document's frontmatter."""

    properties: list[DocumentProperty] = field(default_factory=list)

    @classmethod
    def from_frontmatter(
        cls,
        frontmatter: Mapping[str, Any] | None,
        *,
        cache_default: CachePolicy | None = None,
        disposition_default: str = USER_INFO,
        property_handlers: Iterable[DocumentProperty] | None = None,
    ) -> Self:
        """Create properties and broadcast every frontmatter key to its handlers."""
        result = cls(
            list(property_handlers)
            if property_handlers is not None
            else [
                DocumentCache(default=cache_default or CachePolicy.no_cache()),
                DocumentDisposition(default=disposition_default),
            ]
        )
        for key, value in (frontmatter or {}).items():
            for property in result.properties:
                if property.handles_frontmatter_key(key):
                    property.apply_frontmatter(key, value)
        return result

    def get(self, property_type: type[_DocumentPropertyT]) -> _DocumentPropertyT:
        """Return the registered property of a requested type."""
        return next(property for property in self.properties if isinstance(property, property_type))

    @property
    def cache_policy(self) -> CachePolicy:
        """Return the effective cache policy."""
        return self.get(DocumentCache).value

    @property
    def cache_diagnostic(self) -> str | None:
        """Return any cache declaration diagnostic."""
        return self.get(DocumentCache).diagnostic

    @property
    def disposition(self) -> str | None:
        """Return the effective delivery disposition."""
        return self.get(DocumentDisposition).value

    @classmethod
    def combine(cls, properties: Iterable[Self]) -> Self:
        """Combine matching typed properties across rendered contributors."""
        property_sets = tuple(properties)
        if not property_sets:
            return cls.from_frontmatter(None)
        combined: list[DocumentProperty] = []
        for property in property_sets[0].properties:
            property_type = type(property)
            matching = [
                candidate
                for property_set in property_sets
                for candidate in property_set.properties
                if type(candidate) is property_type
            ]
            combined.append(property_type.combine(matching))
        return cls(combined)


@dataclass
class DocumentContribution:
    """Rendered content and properties contributed to a document delivery."""

    content: str
    frontmatter: Mapping[str, Any]
    properties: DocumentProperties
