"""Feature flag type definitions."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from typing import Any, TypeAlias

from pydantic_core import core_schema

RawFeatureScalar: TypeAlias = bool | str
RawFeatureList: TypeAlias = list[str]
RawFeatureDictValue: TypeAlias = str | list[str]
RawFeatureDict: TypeAlias = dict[str, RawFeatureDictValue]
RawFeatureValue: TypeAlias = RawFeatureScalar | RawFeatureList | RawFeatureDict


def validate_feature_value_type(value: Any) -> bool:
    """Validate that a value matches the supported raw feature flag shapes."""
    if isinstance(value, FeatureValue):
        return True

    if isinstance(value, (bool, str)):
        return True

    if isinstance(value, list):
        return all(isinstance(item, str) for item in value)

    if isinstance(value, dict):
        return all(
            isinstance(key, str)
            and (isinstance(item, str) or (isinstance(item, list) and all(isinstance(entry, str) for entry in item)))
            for key, item in value.items()
        )

    return False


def _ensure_raw_feature_value(value: RawFeatureValue | FeatureValue) -> RawFeatureValue:
    """Return a defensive raw representation of a feature value."""
    if isinstance(value, FeatureValue):
        return value.to_raw()
    if not validate_feature_value_type(value):
        raise TypeError(f"Invalid feature flag value type: {type(value).__name__}")
    return deepcopy(value)


def _format_feature_component(value: Any, *, top_level: bool = False) -> str:
    """Format a raw feature value component for stable display."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value if top_level else repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_format_feature_component(item) for item in value) + "]"
    if isinstance(value, dict):
        items = [f"{repr(key)}: {_format_feature_component(item)}" for key, item in value.items()]
        return "{" + ", ".join(items) + "}"
    return repr(value)


def format_feature_value_for_display(value: RawFeatureValue | FeatureValue) -> str:
    """Render a feature value to a stable user-facing string."""
    return _format_feature_component(_ensure_raw_feature_value(value), top_level=True)


def to_raw_feature_value(value: RawFeatureValue | FeatureValue) -> RawFeatureValue:
    """Convert a feature value or wrapper into a defensive raw value."""
    return _ensure_raw_feature_value(value)


class FeatureValue:
    """Opaque runtime wrapper for feature flag values."""

    __slots__ = ("_value",)

    def __init__(self, value: RawFeatureValue | FeatureValue):
        self._value = _ensure_raw_feature_value(value)

    @classmethod
    def from_raw(cls, value: RawFeatureValue | FeatureValue) -> "FeatureValue":
        """Construct a feature value from a raw supported shape."""
        if isinstance(value, cls):
            return value
        return cls(value)

    def to_raw(self) -> RawFeatureValue:
        """Return a defensive raw representation."""
        return deepcopy(self._value)

    def to_display(self) -> str:
        """Return a stable user-facing string representation."""
        return format_feature_value_for_display(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __iter__(self) -> Iterator[Any]:
        if isinstance(self._value, (list, dict, str)):
            return iter(self._value)
        raise TypeError(f"'{type(self._value).__name__}' object is not iterable")

    def __len__(self) -> int:
        if isinstance(self._value, (list, dict, str)):
            return len(self._value)
        raise TypeError(f"Object of type '{type(self._value).__name__}' has no len()")

    def __contains__(self, item: object) -> bool:
        if isinstance(self._value, str):
            return isinstance(item, str) and item in self._value
        if isinstance(self._value, (list, dict)):
            return item in self._value
        return False

    def __getitem__(self, key: Any) -> Any:
        if isinstance(self._value, (list, dict, str)):
            return self._value[key]
        raise TypeError(f"'{type(self._value).__name__}' object is not subscriptable")

    def get(self, key: str, default: Any = None) -> Any:
        if isinstance(self._value, dict):
            return self._value.get(key, default)
        return default

    def items(self):
        if isinstance(self._value, dict):
            return self._value.items()
        raise AttributeError("items")

    def keys(self):
        if isinstance(self._value, dict):
            return self._value.keys()
        raise AttributeError("keys")

    def values(self):
        if isinstance(self._value, dict):
            return self._value.values()
        raise AttributeError("values")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FeatureValue):
            return self._value == other._value
        if validate_feature_value_type(other):
            return self._value == other
        return False

    def __repr__(self) -> str:
        return f"FeatureValue({self._value!r})"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """Allow pydantic to accept raw values and store wrapped values."""

        def validate(value: Any) -> FeatureValue:
            return cls.from_raw(value)

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(lambda value: value.to_raw()),
        )


FeatureValueLike: TypeAlias = FeatureValue | RawFeatureValue
