from os import PathLike
from typing import Any

from pydantic import BaseModel, Field, field_validator


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
