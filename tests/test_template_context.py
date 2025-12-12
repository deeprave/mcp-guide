"""Tests for template context management."""

from collections import ChainMap

import pytest

from mcp_guide.utils.template_context import TemplateContext


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

    def test_setitem_rejects_non_string_keys(self):
        """Test that __setitem__ rejects non-string keys with TypeError."""
        context = TemplateContext({})

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[123] = "value"

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[3.14] = "value"

        with pytest.raises(TypeError, match="Context keys must be strings"):
            context[None] = "value"

    def test_type_validation_invalid_keys(self):
        """Test that non-string keys raise TypeError."""
        # Test integer keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({123: "value"})

        # Test float keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({3.14: "value"})

        # Test None keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({None: "value"})

        # Test object keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({object(): "value"})

        # Test tuple keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({(1, 2): "value"})

        # Test boolean keys
        with pytest.raises(TypeError, match="Context keys must be strings"):
            TemplateContext({True: "value"})

        # Test list keys (unhashable, but should still be caught)
        with pytest.raises(TypeError):  # Either unhashable or key validation
            bad_dict = {}
            bad_dict[["list"]] = "value"  # Build at runtime to avoid import error
            TemplateContext(bad_dict)

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

    def test_soft_delete_and_hard_delete_methods(self):
        """Test soft_delete() and hard_delete() methods with sentinel masking."""
        parent = TemplateContext({"shared_key": "parent_value", "parent_only": "parent"})
        child = parent.new_child({"shared_key": "child_value", "child_only": "child"})

        # Before deletion - child overrides parent
        assert child["shared_key"] == "child_value"
        assert child["parent_only"] == "parent"
        assert child["child_only"] == "child"

        # Soft delete - key appears missing even if in parent
        child.soft_delete("shared_key")
        with pytest.raises(KeyError):
            _ = child["shared_key"]  # Should raise KeyError even though parent has it

        # soft_delete / hard_delete must reject non-string keys
        ctx = TemplateContext({"k": "v"})
        with pytest.raises(TypeError, match="Context keys must be strings"):
            ctx.soft_delete(123)

        with pytest.raises(TypeError, match="Context keys must be strings"):
            ctx.hard_delete(123)

        # Hard delete - reveals parent value
        child.hard_delete("shared_key")  # Remove soft deletion
        child["shared_key"] = "new_child_value"  # Add it back
        child.hard_delete("shared_key")  # Hard delete
        assert child["shared_key"] == "parent_value"  # Should see parent value

        # Test deletion of key not in parent
        child.soft_delete("child_only")
        with pytest.raises(KeyError):
            _ = child["child_only"]
