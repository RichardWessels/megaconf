"""Sample 16 distinct experiments from a large neural-network search space."""

import random

from megaconf import generate_configs


base = {
    "dataset": "imagenet-1k",
    "seed": 7,
    "trainer": {"epochs": 30, "precision": "bf16"},
}

# creates 55,296 valid configurations
overrides = [{
    "fixed": {"model.type": "vision_transformer"},
    "joint": {
        "model.hidden_dim": [256, 384, 512, 768],
        "model.num_attention_heads": [4, 6, 8, 12],
    },
    "product": {
        "optimizer.name": ["adamw", "lion", "sgd"],
        "optimizer.learning_rate": [1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3],
        "optimizer.weight_decay": [0.0, 0.01, 0.05, 0.1],
        "trainer.batch_size": [32, 64, 128, 256],
        "model.num_layers": [6, 8, 10, 12],
        "model.dropout": [0.0, 0.1, 0.2, 0.3],
        "scheduler.name": ["cosine", "linear", "one_cycle"],
    },
}]

random.seed(42)
configs = generate_configs(
    base,
    overrides,
    sampling="without_replacement",
    n_samples=4,
)

for config in configs:
    print(config)
