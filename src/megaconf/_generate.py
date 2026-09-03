from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter

from ._expansion import get_joint_generator, get_product_generator
from ._inputs import load_data_from_file
from ._models import BaseConfigInput, Override, OverridesInput
from ._utils import convert_flat_dict_to_nested_dict, deep_update_dict


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

        for joint_conf in get_joint_generator(override.joint):
            # NOTE: only product space is sampled
            for prod_conf in get_product_generator(
                override.product, sampling=sampling, n_samples=n_samples
            ):
                new_config = deepcopy(base_config)
                override_dict = fixed | joint_conf | prod_conf

                override_dict = convert_flat_dict_to_nested_dict(
                    override_dict, key_separator
                )
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
        sampling: Optional sampling mode for product combinations.
        n_samples: Number of product combinations to sample.

    Returns:
        An iterator of generated configuration dictionaries.

    Raises:
        TypeError: If base config does not resolve to a dictionary.
    """

    if not isinstance(base_config, dict):
        path = Path(base_config)
        base_config = load_data_from_file(path)

    if isinstance(overrides, (str, Path)):
        path = Path(overrides)
        overrides = load_data_from_file(path)

    # validation
    if not isinstance(base_config, dict):
        raise TypeError("Base config must be a dictionary.")
    overrides_validated = TypeAdapter(list[Override]).validate_python(overrides)

    if (
        not overrides
    ):  # NOTE: need to confirm that this general falsy check is not a problem
        yield base_config
        return

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
        sampling: Optional sampling mode for product combinations.
        n_samples: Number of product combinations to sample.

    Returns:
        All generated configurations materialized in a list.
    """

    return list(
        generate_configs(base_config, overrides, key_separator, sampling, n_samples)
    )
