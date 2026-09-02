"""Generate valid tree and neural-network experiment configs."""

from megaconf import generate_configs

base = {"dataset": "reviews", "seed": 7}

overrides = [
    {
        "fixed": {"model.type": "tree"},
        "joint": {"model.max_depth": [4, 8], "model.min_samples_leaf": [10, 3]},
        "product": {"learning_rate": [0.01, 0.1]},
    },
    {
        "fixed": {"model.type": "neural_net"},
        "joint": {"model.hidden_units": [64, 128], "model.activation": ["relu", "gelu"]},
        "product": {"learning_rate": [10e-3, 10e-4, 10e-5]},
    },
]

for config in generate_configs(base, overrides):
    print(config)
