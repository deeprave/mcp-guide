"""Tests for template context management."""

from collections import ChainMap

import pytest

from mcp_guide.render.context import TemplateContext


class TestTemplateContext:
    """Test TemplateContext class functionality."""

    def test_template_context_extends_chainmap(self):
        """Test that TemplateContext extends ChainMap[str, Any]."""
        context = TemplateContext({"key": "value"})

        # Should be instance of ChainMap
        assert isinstance(context, ChainMap)

        # Should work like ChainMap
        assert context["key"] == "value"
        assert len(context) == 1

    def test_type_validation_valid_keys_and_values(self):
        """Test that valid string keys and template-safe values are accepted."""
        # Valid template-safe types
        valid_data = {
            "string_key": "string_value",
            "int_key": 42,
            "float_key": 3.14,
            "bool_key": True,
            "list_key": ["item1", "item2"],
            "dict_key": {"nested": "value"},
            "none_key": None,
        }

        # Should not raise any exceptions
        context = TemplateContext(valid_data)
        assert len(context) == 7

    def test_setitem_accepts_string_keys(self):
        """Test that __setitem__ accepts string keys."""
        context = TemplateContext({})
        context["valid_key"] = "value"

        assert context["valid_key"] == "value"
        assert len(context) == 1

    def test_setitem_rejects_non_string_keys(self):
        """Test that __setitem__ rejects non-string keys with TypeError."""
        context = TemplateContext({})

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[123] = "value"

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[3.14] = "value"

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[None] = "value"

    @pytest.mark.parametrize(
        "invalid_key",
        [123, 3.14, None, object(), (1, 2), True],
        ids=["int", "float", "none", "object", "tuple", "bool"],
    )
    def test_type_validation_invalid_keys(self, invalid_key):
        """Test that non-string keys raise TypeError."""
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({invalid_key: "value"})

    def test_type_validation_edge_case_keys(self):
        """Test edge cases for string keys that should be valid."""
        # Empty string should be valid (though not recommended)
        context = TemplateContext({"": "empty_key_value"})
        assert context[""] == "empty_key_value"

        # Unicode strings should be valid
        context = TemplateContext({"🔑": "unicode_key", "café": "unicode_value"})
        assert context["🔑"] == "unicode_key"
        assert context["café"] == "unicode_value"

        # Very long string keys should be valid
        long_key = "a" * 1000
        context = TemplateContext({long_key: "long_key_value"})
        assert context[long_key] == "long_key_value"

    def test_new_child_returns_template_context(self):
        """Test that new_child() returns TemplateContext instances."""
        parent = TemplateContext({"parent_key": "parent_value"})
        child = parent.new_child({"child_key": "child_value"})

        # Should return TemplateContext instance, not just ChainMap
        assert isinstance(child, TemplateContext)
        assert type(child) == TemplateContext  # Exact type check

        # Should work like ChainMap with scope chaining
        assert child["child_key"] == "child_value"
        assert child["parent_key"] == "parent_value"

        # Child should override parent

    def test_parents_property_returns_template_context(self):
        """Test that parents property returns TemplateContext | None."""
        # Root context should have None parents
        root = TemplateContext({"root": "value"})
        assert root.parents is None

        # Child context should have TemplateContext parents
        child = root.new_child({"child": "value"})
        assert isinstance(child.parents, TemplateContext)
        assert child.parents["root"] == "value"

        # Grandchild should also have TemplateContext parents
        grandchild = child.new_child({"grandchild": "value"})
        assert isinstance(grandchild.parents, TemplateContext)
