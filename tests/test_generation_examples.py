from __future__ import annotations

from copy import deepcopy
from itertools import product
from pathlib import Path

import pytest
from pydantic import ValidationError
from yaml import safe_dump

from src.generate import generate_configs, generate_configs_list


@pytest.fixture
def base_config() -> dict:
    return {
        "model": {"name": "nn", "type": "classification"},
        "train": {"lr": 0.001, "batch_size": 32, "epochs": 100},
        "data": {"seed": 42},
    }


class TestCommonBehavior:
    def test_empty_override_block_outputs_base_config(self, base_config: dict):
        results = generate_configs_list(base_config, [{}])

        assert results == [base_config]

    def test_none_overrides_raise_validation_error(self, base_config: dict):
            with pytest.raises(ValidationError):
                _ = generate_configs_list(base_config, None)

    def test_base_and_overrides_are_not_mutated(self, base_config: dict):
            overrides = [{"fixed": {"train.lr": 0.5}}]
            base_before = deepcopy(base_config)
            overrides_before = deepcopy(overrides)
    
            _ = generate_configs_list(base_config, overrides)
    
            assert base_config == base_before
            assert overrides == overrides_before


class TestFixedOverrides:
    def test_fixed_overrides_replace_and_add(self, base_config: dict):
        overrides = [{"fixed": {"model.type": "regression", "train.weight_decay": 0.01}}]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 1
        assert results[0]["model"]["type"] == "regression"
        assert results[0]["train"]["weight_decay"] == 0.01


class TestJointOverrides:
    def test_joint_generates_sequential_pairs(self, base_config: dict):
        overrides = [
            {
                "joint": {
                    "train.lr": [0.1, 0.01],
                    "model.name": ["small", "large"],
                }
            }
        ]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 2
        assert results[0]["train"]["lr"] == 0.1
        assert results[0]["model"]["name"] == "small"
        assert results[1]["train"]["lr"] == 0.01
        assert results[1]["model"]["name"] == "large"

    def test_joint_mismatched_lengths_raise(self, base_config: dict):
        overrides = [{"joint": {"train.lr": [0.1], "model.name": ["a", "b"]}}]

        with pytest.raises(ValueError):
            _ = list(generate_configs(base_config, overrides))


class TestProductOverrides:
    def test_product_generates_cartesian_product(self, base_config: dict):
        overrides = [
            {
                "product": {
                    "train.lr": [0.1, 0.01],
                    "train.epochs": [10, 20, 30],
                }
            }
        ]

        results = generate_configs_list(base_config, overrides)

        expected_pairs = list(product([0.1, 0.01], [10, 20, 30]))
        assert len(results) == len(expected_pairs)
        actual_pairs = {(cfg["train"]["lr"], cfg["train"]["epochs"]) for cfg in results}
        assert actual_pairs == set(expected_pairs)

    def test_product_with_empty_list_yields_no_configs(self, base_config: dict):
        overrides = [{"product": {"train.lr": [0.1], "train.epochs": []}}]

        results = generate_configs_list(base_config, overrides)

        assert results == []


class TestCombinedBehavior:
    # TODO: test value rather than just count
    def test_fixed_joint_product_can_be_combined(self, base_config: dict):
        overrides = [
            {
                "fixed": {"model.type": "fixed"},
                "joint": {"model.type": ["joint-1", "joint-2"], "train.lr": [0.1, 0.01]},
                "product": {"model.type": ["prod-a", "prod-b"], "train.epochs": [10, 20]},
            }
        ]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 8

    # TODO: this will be changed in future to allow for a given order precedence
    def test_priority_product_then_joint_then_fixed(self, base_config: dict):
        overrides = [
            {
                "fixed": {"model.type": "from-fixed"},
                "joint": {"model.type": ["from-joint"]},
                "product": {"model.type": ["from-product"]},
            }
        ]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 1
        assert results[0]["model"]["type"] == "from-product"

    def test_fixed_applies_before_product_within_override_block(self, base_config: dict):
        overrides = [{"fixed": {"model.type": "one"}, "product": {"train.lr": [0.1, 0.01]}}]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 2
        assert all(cfg["model"]["type"] == "one" for cfg in results)
        assert {cfg["train"]["lr"] for cfg in results} == {0.1, 0.01}


class TestInputModes:
    def test_generate_configs_returns_generator(self, base_config: dict):
        overrides = [{"fixed": {"train.lr": 0.1}}]

        results = generate_configs(base_config, overrides)

        assert iter(results) is results

    def test_config_dict_and_override_dict(self, base_config: dict):
        overrides = [{"fixed": {"train.lr": 0.1}}]

        results = generate_configs_list(base_config, overrides)

        assert len(results) == 1
        assert results[0]["train"]["lr"] == 0.1

    def test_config_dict_and_override_file(self, base_config: dict, tmp_path: Path):
        overrides_payload = [{"joint": {"train.lr": [0.1, 0.01]}}]
        overrides_path = tmp_path / "overrides.yaml"
        overrides_path.write_text(safe_dump(overrides_payload), encoding="utf-8")

        results = generate_configs_list(base_config, overrides_path)

        assert len(results) == 2

    def test_config_file_and_override_dict(self, base_config: dict, tmp_path: Path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(safe_dump(base_config), encoding="utf-8")

        results = generate_configs_list(
            config_path, [{"product": {"train.epochs": [1, 2, 3]}}]
        )

        assert len(results) == 3

    def test_single_combined_file(self, tmp_path: Path):
        pass  # TODO: functionality still being worked on
        # payload = {
        #     "base": {"k1": "v1", "k2": {"k3": "v2"}},
        #     "overrides": [{"joint": {"k1": ["a", "b"], "k2.k3": ["x", "y"]}}],
        # }
        # file_path = tmp_path / "combined.yaml"
        # file_path.write_text(safe_dump(payload), encoding="utf-8")

        # results = generate_configs_list(file_path)

        # assert len(results) == 2
        # assert results[0]["k1"] == "a"
        # assert results[0]["k2"]["k3"] == "x"
        # assert results[1]["k1"] == "b"
        # assert results[1]["k2"]["k3"] == "y"
