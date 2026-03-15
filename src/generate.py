import json
from copy import deepcopy
from itertools import product
from os import PathLike
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, TypeAdapter
from yaml import safe_load

from src.utils import convert_flat_dict_to_nested_dict, deep_update_dict


class Override(BaseModel):  # pylint: disable=missing-class-docstring
    # add validation logic to ensure joint has equal length lists
    fixed: dict = Field(default_factory=dict)
    joint: dict[str, list] = Field(default_factory=dict)
    product: dict[str, list] = Field(default_factory=dict)


type ConfigDict = dict[str, Any]
type BaseConfigInput = ConfigDict | str | PathLike[str]
type OverridesInput = list[dict[str, Any]] | str | PathLike[str]


def _expand_joint(joint: dict[str, list]) -> list[dict]:
    # expand joint

    if not joint:
        return []

    if len(np.unique([len(joint_value) for joint_value in joint.values()])) > 1:
        raise ValueError("Joint update requires lists of equal length")

    joint_expanded = []
    for key, value in joint.items():
        joint_expanded.append([(key, value) for value in value])

    joint_expanded = list(zip(*joint_expanded, strict=True))

    return [dict(e) for e in joint_expanded]


def _expand_product(prod: dict[str, list]) -> list[dict]:
    # TODO: should change later since expanding this is high memory

    product_expanded = []
    for key, value in prod.items():
        product_expanded.append([(key, v) for v in value])
    product_expanded = list(product(*product_expanded))

    return [dict(e) for e in product_expanded]


def _load_data_from_file(file_path: Path | str) -> Any:
    file_path = Path(file_path)

    with open(file_path, encoding="utf-8") as f:
        if file_path.suffix in [".yaml", ".yml"]:
            return safe_load(f)
        if file_path.suffix == ".json":
            return json.load(f)
        raise ValueError("File must end in `.yaml`, `.yml` or `.json`.")


def generate_configs(
    base_config: BaseConfigInput, overrides: OverridesInput | None, key_separator="."
) -> list:
    if not overrides:  # NOTE: need to confirm that this general falsy check is not a problem
        return []

    if not isinstance(base_config, dict):
        path = Path(base_config)
        base_config = _load_data_from_file(path)

    if not isinstance(overrides, list):
        path = Path(overrides)
        overrides = _load_data_from_file(path)

    # validation
    if not isinstance(base_config, dict):
        raise ValueError("Base config must be a dictionary.")
    overrides_validated = TypeAdapter(list[Override]).validate_python(overrides)

    return _generate_configs(base_config, overrides_validated, key_separator)


def _generate_configs(base_config: dict, overrides: list[Override], key_separator: str) -> list:
    outputs = []

    for override in overrides:
        fixed_expanded = [override.fixed]
        joint_expanded = _expand_joint(override.joint) or [{}]
        prod_expanded = _expand_product(override.product) or [{}]

        for fixed_item, joint_item, prod_item in product(
            fixed_expanded, joint_expanded, prod_expanded
        ):
            if not fixed_item and not joint_item and not prod_item:
                continue
            new_config = deepcopy(base_config)

            updated_dict = fixed_item | joint_item | prod_item
            updated_dict = convert_flat_dict_to_nested_dict(updated_dict, key_separator)
            new_config = deep_update_dict(new_config, updated_dict)

            outputs.append(new_config)

    return outputs
