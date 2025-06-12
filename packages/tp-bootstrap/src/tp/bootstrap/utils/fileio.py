from __future__ import annotations

import yaml
from typing import Any


def load_yaml(file_path: str) -> dict[str, Any] | list[Any] | None:
    """Function that loads and returns the data of YAML file.

    Args:
        file_path: The path to the YAML file.

    Returns:
        The data loaded from the YAML file.
    """

    with open(file_path, "r", encoding="utf-8") as yaml_file:
        return yaml.safe_load(yaml_file)
