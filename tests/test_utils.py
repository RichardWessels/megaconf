from copy import deepcopy

import pytest

from megaconf.exceptions import FlatKeyConflictError
from megaconf.utils import convert_flat_dict_to_nested_dict, deep_update_dict


class TestConvertFlatDictToNestedDict:
    def test_empty_dict(self):
        assert convert_flat_dict_to_nested_dict({}) == {}

    def test_single_flat_key(self):
        assert convert_flat_dict_to_nested_dict({"a": 1}) == {"a": 1}

    def test_single_nested_key(self):
        assert convert_flat_dict_to_nested_dict({"a.b": 1}) == {"a": {"b": 1}}

    def test_multiple_nested_keys_same_parent(self):
        result = convert_flat_dict_to_nested_dict(
            {
                "a.b": 1,
                "a.c": 2,
            }
        )
        assert result == {"a": {"b": 1, "c": 2}}

    def test_multiple_nested_keys_different_parents(self):
        result = convert_flat_dict_to_nested_dict(
            {
                "a.b": 1,
                "x.y": 2,
            }
        )
        assert result == {"a": {"b": 1}, "x": {"y": 2}}

    def test_deeply_nested_keys(self):
        result = convert_flat_dict_to_nested_dict({"a.b.c.d": 1})
        assert result == {"a": {"b": {"c": {"d": 1}}}}

    def test_custom_separator(self):
        result = convert_flat_dict_to_nested_dict(
            {"a/b/c": 1, "a/b/d": 2},
            key_separator="/",
        )
        assert result == {"a": {"b": {"c": 1, "d": 2}}}

    def test_conflict_parent_already_scalar_raises(self):
        with pytest.raises(FlatKeyConflictError, match="Duplicate key found"):
            convert_flat_dict_to_nested_dict(
                {
                    "a": 1,
                    "a.b": 2,
                }
            )

    def test_conflict_parent_already_scalar_can_override(self):
        result = convert_flat_dict_to_nested_dict(
            {
                "a": 1,
                "a.b": 2,
            },
            override_duplicates=True,
        )
        assert result == {"a": {"b": 2}}

    def test_leaf_overwrites(self):
        with pytest.raises(FlatKeyConflictError, match="Duplicate key found"):
            convert_flat_dict_to_nested_dict(
                {
                    "a.b": 1,
                    "a": 2,
                }
            )

    def test_non_conflicting_mixed_top_level_and_nested_keys(self):
        result = convert_flat_dict_to_nested_dict(
            {
                "a.b": 1,
                "x": 2,
                "y.z": 3,
            }
        )
        assert result == {
            "a": {"b": 1},
            "x": 2,
            "y": {"z": 3},
        }


class TestDeepUpdateDict:
    def test_replaces_top_level_value(self):
        base = {"a": 1, "b": 2}
        override = {"b": 99}

        result = deep_update_dict(base, override)

        assert result == {"a": 1, "b": 99}

    def test_adds_new_top_level_key(self):
        base = {"a": 1}
        override = {"b": 2}

        result = deep_update_dict(base, override)

        assert result == {"a": 1, "b": 2}

    def test_recursively_updates_nested_dict(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 99, "z": 100}}

        result = deep_update_dict(base, override)

        assert result == {"a": {"x": 1, "y": 99, "z": 100}, "b": 3}

    def test_replaces_non_dict_with_dict(self):
        base = {"a": 1}
        override = {"a": {"x": 10}}

        result = deep_update_dict(base, override)

        assert result == {"a": {"x": 10}}

    def test_replaces_dict_with_non_dict(self):
        base = {"a": {"x": 1}}
        override = {"a": 42}

        result = deep_update_dict(base, override)

        assert result == {"a": 42}

    def test_override_empty_returns_copy_of_base(self):
        base = {"a": 1, "b": {"x": 2}}
        override = {}

        result = deep_update_dict(base, override)

        assert result == base
        assert result is not base
        assert result["b"] is not base["b"]

    def test_base_empty_returns_override_contents(self):
        base = {}
        override = {"a": 1, "b": {"x": 2}}

        result = deep_update_dict(base, override)

        assert result == {"a": 1, "b": {"x": 2}}

    def test_does_not_mutate_base(self):
        base = {"a": {"x": 1}, "b": 2}
        override = {"a": {"x": 99}, "c": 3}
        base_before = deepcopy(base)

        _ = deep_update_dict(base, override)

        assert base == base_before
