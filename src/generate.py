import json
import random
from collections.abc import Iterator
from copy import deepcopy
from os import PathLike
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, TypeAdapter, field_validator
from yaml import safe_load

from src.utils import convert_flat_dict_to_nested_dict, deep_update_dict


class Override(BaseModel):
    fixed: dict[str, Any] = Field(default_factory=dict)
    joint: dict[str, list] = Field(default_factory=dict)
    product: dict[str, list] = Field(default_factory=dict)

    @field_validator("joint")
    @classmethod
    def validate_joint_lengths(cls, joint: dict[str, list]):
        """Validate that all lists in ``joint`` have equal length.

        Args:
            joint: Mapping of override keys to lists.

        Returns:
            The validated ``joint`` mapping.

        Raises:
            ValueError: If list lengths differ across ``joint`` keys.
        """
        lengths = {key: len(value) for key, value in joint.items()}

        if len(set(lengths.values())) > 1:
            raise ValueError(f"All lists in 'joint' must have equal length. Got lengths: {lengths}")

        return joint


type ConfigDict = dict[str, Any]
type BaseConfigInput = ConfigDict | str | PathLike[str]
type OverridesInput = list[dict[str, Any]] | str | PathLike[str]


def _load_data_from_file(file_path: Path | str) -> Any:
    """Load YAML or JSON data from disk.

    Args:
        file_path: Path to a ``.yaml``, ``.yml``, or ``.json`` file.

    Returns:
        Parsed file contents.

    Raises:
        ValueError: If the file extension is unsupported.
    """
    file_path = Path(file_path)

    with open(file_path, encoding="utf-8") as f:
        if file_path.suffix in [".yaml", ".yml"]:
            return safe_load(f)
        if file_path.suffix == ".json":
            return json.load(f)
        raise ValueError("File must end in `.yaml`, `.yml` or `.json`.")


def _get_joint_generator(joint_config: dict[str, list]) -> Iterator[dict]:
    """Yield joint overrides by zipping aligned list values.

    Args:
        joint_config: Mapping of keys to equally sized lists.

    Yields:
        Dictionaries containing one value per key at each shared index.
    """
    if not joint_config:
        yield {}
        return

    list_length = len(next(iter(joint_config.values())))

    for i in range(list_length):
        yield {k: v[i] for k, v in joint_config.items()}


def _get_product_generator(
    product_config: dict[str, list],
    sampling: Literal["without_replacement", "with_replacement"] | None = None,
    n_samples: int | None = None,
) -> Iterator[dict]:
    """Yield product overrides from the Cartesian product of list values.

    Args:
        product_config: Mapping of keys to candidate values.
        sampling: Optional sampling mode over product indices.
        n_samples: Number of sampled combinations when sampling is enabled.

    Yields:
        Dictionaries containing one chosen value per product key.

    Raises:
        ValueError: If sampling is enabled without ``n_samples`` or mode is invalid.
    """

    if not product_config:
        yield {}
        return

    prod_items = product_config.items()
    prod_keys = [item[0] for item in prod_items]
    prod_values = [item[1] for item in prod_items]

    n = int(np.prod([len(it) for it in prod_values]))

    if sampling is None:
        loop_values = range(n)
    else:
        if n_samples is None:
            raise ValueError("Argument `n_samples` required when using sampling.")
        if sampling == "with_replacement":
            loop_values = random.choices(range(n), k=n_samples)
        elif sampling == "without_replacement":
            loop_values = random.sample(range(n), k=n_samples)
        else:
            # illegal state
            raise ValueError("Invalid value for `sampling` given.")

    for num in loop_values:
        i = num

        res = []
        for it in reversed(prod_values):
            i, r = divmod(i, len(it))
            res.append(it[r])
        res = list(reversed(res))

        yield {prod_keys[i]: res[i] for i in range(len(prod_keys))}


def _generate_configs(
    base_config: dict,
    overrides: list[Override],
    key_separator: str,
    sampling: Literal["without_replacement", "with_replacement"] | None = None,
    n_samples: int | None = None,
) -> Iterator[dict]:
    """Generate merged configs for all fixed, joint, and product combinations.

    Args:
        base_config: Base configuration to copy and update.
        overrides: Validated override groups.
        key_separator: Separator for flat keys that target nested fields.
        sampling: Optional sampling mode for product combinations.
        n_samples: Number of product combinations to sample.

    Yields:
        Fully merged configuration dictionaries.
    """

    for override in overrides:
        fixed = override.fixed

        for joint_conf in _get_joint_generator(override.joint):
            # NOTE: only product space is sampled
            for prod_conf in _get_product_generator(
                override.product, sampling=sampling, n_samples=n_samples
            ):
                new_config = deepcopy(base_config)
                override_dict = fixed | joint_conf | prod_conf

                override_dict = convert_flat_dict_to_nested_dict(override_dict, key_separator)
                new_config = deep_update_dict(new_config, override_dict)

                yield new_config


def generate_configs(
    base_config: BaseConfigInput,
    overrides: OverridesInput | None,
    key_separator=".",
    sampling: Literal["without_replacement", "with_replacement"] | None = None,
    n_samples: int | None = None,
) -> Iterator[dict]:
    """Generate configurations from a base config and override definitions.

    Args:
        base_config: Base config dictionary or path to YAML/JSON.
        overrides: Override list or path to YAML/JSON override definitions.
        key_separator: Separator used in flat override keys for nesting.

    Returns:
        An iterator of generated configuration dictionaries.

    Raises:
        ValueError: If base config does not resolve to a dictionary.
    """

    if not isinstance(base_config, dict):
        path = Path(base_config)
        base_config = _load_data_from_file(path)

    if isinstance(overrides, (str, Path)):
        path = Path(overrides)
        overrides = _load_data_from_file(path)

    # validation
    if not isinstance(base_config, dict):
        raise ValueError("Base config must be a dictionary.")
    overrides_validated = TypeAdapter(list[Override]).validate_python(overrides)

    if not overrides:  # NOTE: need to confirm that this general falsy check is not a problem
        yield base_config
        return

    # configs = _generate_configs(base_config, overrides_validated, key_separator)

    # for conf in configs:
    #     print(conf)

    yield from _generate_configs(
        base_config, overrides_validated, key_separator, sampling, n_samples
    )


def generate_configs_list(
    base_config: BaseConfigInput,
    overrides: OverridesInput | None,
    key_separator=".",
    sampling: Literal["without_replacement", "with_replacement"] | None = None,
    n_samples: int | None = None,
) -> list[dict]:
    """Return generated configurations as a list.

    Args:
        base_config: Base config dictionary or path to YAML/JSON.
        overrides: Override list or path to YAML/JSON override definitions.
        key_separator: Separator used in flat override keys for nesting.

    Returns:
        All generated configurations materialized in a list.
    """

    return list(generate_configs(base_config, overrides, key_separator, sampling, n_samples))
