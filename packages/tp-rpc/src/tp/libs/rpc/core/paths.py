from __future__ import annotations

import platform
from pathlib import Path


def get_registry_path() -> Path:
    """Function that returns the platform-specific path to the
    persistent registry file.

    Returns:
        The absolute path to the registry JSON file.
    """

    if platform.system() == "Windows":
        base_dir = Path.home() / "AppData" / "Roaming"
    else:
        base_dir = Path.home() / ".config"

    registry_dir = base_dir / "tp_dcc_rpc"
    registry_dir.mkdir(parents=True, exist_ok=True)

    return registry_dir / "registry.json"


def get_config_path() -> Path:
    """Function that returns the platform-specific path to the
    configuration file.

    Returns:
        The absolute path to the configuration JSON file.
    """

    if platform.system() == "Windows":
        base_dir = Path.home() / "AppData" / "Roaming"
    else:
        base_dir = Path.home() / ".config"

    config_dir = base_dir / "tp_dcc_rpc"
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / "config.json"
