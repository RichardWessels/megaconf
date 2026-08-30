# MegaConf

MegaConf is a tool to help with producing configs. This tool allows you to describe configuration combinations declaratively, instead of writing nested loops in code.

## How it works

MegaConf generates configurations from two inputs:

1. Base config – a starting configuration.
2. Override config – rules describing how to modify the base config to produce multiple variants.

The result is a set of generated configs.

## Example

Suppose we start with a base config:

```yaml
algo: NN
lr: 0.001
layer_count: 8
activation: ReLU
initializer: He
```

We want to run experiments across different algorithms and hyperparameters.

This might look like:

```python
for algo in ["XGBoost", "NN"]:
    for lr in [0.1, 0.01, 0.001]:
        if algo == "NN":
            for layer_count in [4, 8, 12, 16]:
                for activation in ["ReLU", "Tanh"]:
                    ...
```

As the number of parameters and dependencies grows, this approach becomes hard to maintain.

MegaConf allows expressing the same logic using override rules.

Override Config:
```yaml
- fixed:
    algo: XGBoost
  product:
    lr: [0.1, 0.01, 0.001]

- fixed:
    algo: NN
  joint:
    activation: [ReLU, Tanh]
    initializer: [He, Glorot]
  product:
    lr: [0.1, 0.01, 0.001]
    layer_count: [4, 8, 12, 16]
```

## Override Methods

MegaConf supports three override methods.

---

### `fixed`

Sets specific values in the config.

```yaml
fixed:
  algo: NN
```

Equivalent to:

```python
config["algo"] = "NN"
```

If the key does not exist in the base config, it is added.

---

### `joint`

Iterates over multiple parameters together.

All lists must be the same length.

```yaml
joint:
  activation: [ReLU, Tanh]
  initializer: [He, Glorot]
```

Result:
```
activation=ReLU  initializer=He
activation=Tanh  initializer=Glorot
```

This is useful for paired parameters.

---

### `product`

Produces the cartesian product of parameter values.

```yaml
product:
  lr: [0.1, 0.01, 0.001]
  layer_count: [4, 8, 12]
```

This generates:

```
lr=0.1   layer_count=4
lr=0.1   layer_count=8
lr=0.1   layer_count=12
lr=0.01  layer_count=4
...
```

This is equivalent to a grid search.

## How Overrides Are Combined

Within an override block:

1. fixed values are applied first.
2. joint combinations are generated.
3. product combinations are generated.

The final configs are the combination of these rules applied to the base config.

## Interface

Creating configs is done with the function `generate_configs`. It accepts a base config as well as an overrides config. 

Both inputs can be provided in two ways:
- as a Python object (e.g., a dictionary or list).
- as a path to a configuration file (.yaml, .yml, or .json).

The result of this function is a list with each element containing a generated config. The number of generated configs depends on the combinations produced by the override rules.

Example usage:

```python
base_config = {
    "algo": "NN",
    "lr": 0.001,
    "layer_count": 8,
    "activation": "ReLU",
    "initializer": "He"
}

overrides = [
    {
        "fixed": {
            "algo": "XGBoost"
        },
        "product": {
            "lr": [0.1, 0.01, 0.001]
        }
    },
    {
        "fixed": {
            "algo": "NN"
        },
        "joint": {
            "activation": ["ReLU", "Tanh"],
            "initializer": ["He", "Glorot"]
        },
        "product": {
            "lr": [0.1, 0.01],
            "layer_count": [4, 8]
        }
    }
]

configs = generate_configs(base_config, overrides)
```

Or if the base and overrides separate config files:
```python
configs = generate_configs(
    "base_config.yaml",
    "overrides.yaml"
)
```

## Nesting
If a key is deeply nested in the config, a dot-key separator is used by default. This means that specifying a nested key is done as follows:
```yaml
fixed:
  key1.key2.key3: value
```
However, if a dot conflicts with your key strings, you can specify a custom key separator as follows:
```python
configs = generate_configs(
    "base_config.yaml",
    "overrides.yaml",
    key_separator="::"
)
```
