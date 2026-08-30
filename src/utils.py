from copy import deepcopy
from typing import Any


def convert_flat_dict_to_nested_dict(
    dictionary: dict[str, Any], key_separator=".", override_duplicates=False
) -> dict:
    """
    Convert from format: {"k1.k2": value} -> {"k1": {"k2": value}}
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
                    raise RuntimeError(
                        f"Duplicate key found: '{composite_key}'. "
                        "Set `override_duplicates`=True to skip this error."
                    )
            current_dict[key] = current_dict.get(key, {})
            current_dict = current_dict[key]

        # write value
        key = key_list[-1]
        if key in current_dict and not override_duplicates:
            raise RuntimeError(
                f"Duplicate key found: '{composite_key}'. "
                "Set `override_duplicates`=True to skip this error."
            )
        current_dict[key] = value
    return output_dict


def deep_update_dict(base: dict, override: dict) -> dict:
    """
    Recursively replaces each key/value in `base` that is also present in `override`
    When key not in `base`, adds the key.
    """
    output = deepcopy(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = deep_update_dict(output[key], value)
        else:
            output[key] = deepcopy(value)

    return output
