import json
from pathlib import Path
from typing import Any

from yaml import safe_load


def load_data_from_file(file_path: Path | str) -> Any:
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
