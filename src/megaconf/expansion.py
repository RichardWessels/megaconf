import random
from collections.abc import Iterator
from typing import Literal

import numpy as np

def get_joint_generator(joint_config: dict[str, list]) -> Iterator[dict]:
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


def get_product_generator(
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
        ValueError: If sampling options are invalid.
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
            raise ValueError(
                "`n_samples` required when using sampling."
            )
        if n_samples < 0:
            raise ValueError("`n_samples` must be non-negative.")
        if sampling == "without_replacement" and n_samples > n:
            raise ValueError(
                "`n_samples` cannot exceed the product size when sampling "
                "without replacement."
            )
        if n == 0 and n_samples > 0:
            raise ValueError(
                "Cannot sample from a product containing an empty value list."
            )
        if sampling == "with_replacement":
            loop_values = random.choices(range(n), k=n_samples)
        elif sampling == "without_replacement":
            loop_values = random.sample(range(n), k=n_samples)
        else:
            raise ValueError("Invalid value for `sampling` given.")

    for num in loop_values:
        i = num

        res = []
        for it in reversed(prod_values):
            i, r = divmod(i, len(it))
            res.append(it[r])
        res = list(reversed(res))

        yield {prod_keys[i]: res[i] for i in range(len(prod_keys))}
