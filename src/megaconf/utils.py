from copy import deepcopy
from typing import Any

from .exceptions import FlatKeyConflictError


def convert_flat_dict_to_nested_dict(
    dictionary: dict[str, Any], key_separator=".", override_duplicates=False
) -> dict:
    """Convert a dictionary with separator-delimited keys into nested dictionaries.

    Example: ``{"k1.k2": value} -> {"k1": {"k2": value}}``.

    Args:
        dictionary: Mapping of flattened keys to values.
        key_separator: String used to split each flattened key into path segments.
        override_duplicates: Whether to replace conflicts instead of raising an
            error.

    Returns:
        A newly constructed dictionary with keys expanded into nested
        dictionaries.

    Raises:
        FlatKeyConflictError: If flattened keys define conflicting paths and
            ``override_duplicates`` is ``False``.
    """
    output_dict = {}

    for composite_key, value in dictionary.items():
        current_dict = output_dict
        key_list = composite_key.split(key_separator)

        # step through dictionary
        for key in key_list[:-1]:
            if key in current_dict and not isinstance(current_dict[key], dict):
                if override_duplicates:
                    current_dict[key] = {}
                else:
                    raise FlatKeyConflictError(
                        f"Duplicate key found: '{composite_key}'. "
                        "Set `override_duplicates=True` to skip this error."
                    )
            current_dict[key] = current_dict.get(key, {})
            current_dict = current_dict[key]

        # write value
        key = key_list[-1]
        if key in current_dict and not override_duplicates:
            raise FlatKeyConflictError(
                f"Duplicate key found: '{composite_key}'. "
                "Set `override_duplicates=True` to skip this error."
            )
        current_dict[key] = value
    return output_dict


def deep_update_dict(base: dict, override: dict) -> dict:
    """Deep merge an override dictionary into a deep copy of a base dictionary.

    Args:
        base: Dictionary providing the initial values.
        override: Dictionary whose values take precedence over ``base``.

    Returns:
        A deep-copied merge of ``base`` and ``override``.
    """
    output = deepcopy(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = deep_update_dict(output[key], value)
        else:
            output[key] = deepcopy(value)

    return output
