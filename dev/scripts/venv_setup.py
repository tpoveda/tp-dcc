"""This script automates the creation and setup of a Python virtual
environment (venv) using the UV package manager. It is designed to work in a
structured project layout, automating repetitive manual steps such as
environment creation and dependency installation.

Key features:
- Resolves paths dynamically relatively to the script location.
- Uses a specified Python interpreter to create the virtual environment.
- Installs base and development dependencies from pyproject.toml via UV.
- Automatically skips environment creation if the venv already exists.

Requirements:
- UV must be installed and accessible in the system PATH.
- Python 3.7+ (due to pathlib and subprocess usage).
"""

from __future__ import annotations

import os
import sys
import shutil
import logging
import argparse
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

venv_setups = {
    "dev": {
        "python": "C:/Python311/python.exe",
        "name": "dev-3.11.8",
    },
    "maya2026": {
        "python": "C:/Python311/python.exe",
        "name": "maya2026",
    },
    "ue5": {
        "python": "C:/Python311/python.exe",
        "name": "ue5",
    },
    "mobu2026": {
        "python": "C:/Python311/python.exe",
        "name": "mobu2026",
    },
    "hou20522": {
        "python": "C:/Python311/python.exe",
        "name": "hou20522",
    },
}


def create_venv(python_exe: Path, venv_dir: Path):
    """Creates a new virtual environment using UV.

    Args:
        python_exe: Path to the Python executable to use for creating the venv.
        venv_dir: Path to the virtual environment directory.
    """

    logger.info(f"Creating virtual environment at: {venv_dir}")
    result = subprocess.run(
        ["uv", "venv", "--python", str(python_exe), str(venv_dir)],
        check=False,
    )
    if result.returncode != 0:
        logger.error("Failed to create virtual environment.")
        if venv_dir.exists():
            logger.warning(f"Cleaning up incomplete venv at: {venv_dir}")
            shutil.rmtree(venv_dir, ignore_errors=True)
        sys.exit(1)


def activate_virtualenv(venv_dir: Path):
    """Modify environment variables to simulate activating the venv.

    Args:
        venv_dir: Path to the virtual environment directory.
    """

    venv_scripts = venv_dir / "Scripts"  # Windows
    if not venv_scripts.exists():
        venv_scripts = venv_dir / "bin"  # Linux/macOS fallback

    os.environ["VIRTUAL_ENV"] = str(venv_dir)
    os.environ["PATH"] = str(venv_scripts) + os.pathsep + os.environ["PATH"]
    logger.info(f"Activated virtual environment at: {venv_dir}")


def install_dependencies(pyproject_file: Path, env: str):
    """Installs project dependencies from pyproject.toml using UV.

    Args:
        pyproject_file: Path to the pyproject.toml file.
        env: The target environment to install dependencies
            for (dev, maya2025 ...).
    """

    if not pyproject_file.exists():
        logger.error(f"pyproject.toml not found: {pyproject_file}")
        sys.exit(1)

    logger.info(f"Installing dependencies from {pyproject_file} (UV)...")
    cmd = ["uv", "pip", "install", "-r", str(pyproject_file)]
    cmd += ["--extra", env]

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        logger.error("Failed to install dependencies from pyproject.toml.")
        sys.exit(1)


def install_packages(package_paths: list[Path]):
    """Installs local packages in editable mode.

    Args:
        package_paths: List of paths to package directories.
    """

    for package_path in package_paths:
        if package_path.exists():
            logger.info(f"Installing local package: {package_path}")
            result = subprocess.run(
                ["uv", "pip", "install", "-e", str(package_path)],
                check=False,
            )
            if result.returncode != 0:
                logger.error(f"Failed to install package: {package_path}")
                sys.exit(1)
        else:
            logger.warning(f"Package path does not exist: {package_path}")


def main():
    """Main function to handle command-line arguments and manage the venv."""

    logger.info("Starting setup...")

    parser = argparse.ArgumentParser(
        description="Manage development virtual environment."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--create",
        action="store_true",
        help="Create and setup the venv from scratch.",
    )
    group.add_argument(
        "--update",
        action="store_true",
        help="Update existing venv with latest dependencies.",
    )
    parser.add_argument(
        "--env",
        required=True,
        help="Target environment to manage (e.g., dev, maya2025, ue5).",
    )
    parser.add_argument(
        "--skip-packages",
        action="store_true",
        help="Skip installing local packages.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of the venv if it exists.",
    )
    args = parser.parse_args()

    # Resolve paths.
    script_dir = Path(__file__).parent
    root_dir = (script_dir / "../..").resolve()

    if args.env not in venv_setups:
        logger.error(
            f"Invalid environment '{args.env}'. "
            f"Available options: {list(venv_setups.keys())}"
        )
        sys.exit(1)

    # Configuration.
    setup_config = venv_setups[args.env]
    python_exe_path = setup_config["python"]
    venv_name = setup_config["name"]
    venv_dir = root_dir / "envs" / venv_name
    dev_dir = root_dir / "dev"  # <-- dev folder with pyproject.toml
    pyproject_file = dev_dir / "pyproject.toml"
    package_paths = [
        path
        for path in (root_dir / "packages").iterdir()
        if path.is_dir() and path.name.startswith("tp-")
    ]

    logger.info(f"Using Python: {python_exe_path}")
    logger.info(f"Creating venv (UV): {venv_name}")

    # Check if venv already exists.
    if args.create:
        if venv_dir.exists():
            if args.force:
                logger.warning(f"Venv already exists. Forcing recreation: {venv_dir}")
                shutil.rmtree(venv_dir, ignore_errors=True)
            else:
                logger.warning(f"Venv already exists at: {venv_dir}")
                logger.info("If you want to recreate it, use --force.")
                sys.exit(1)

        logger.info("Starting venv creation...")
        create_venv(python_exe_path, venv_dir)
        activate_virtualenv(venv_dir)
        install_dependencies(pyproject_file, args.env)
        if not args.skip_packages:
            install_packages(package_paths)
        logger.info(f"Venv {venv_name} created and configured successfully!")

    elif args.update:
        if not venv_dir.exists():
            logger.error(f"Venv does not exist: {venv_dir}")
            sys.exit(1)

        logger.info("Starting venv update...")
        activate_virtualenv(venv_dir)
        install_dependencies(pyproject_file, env=args.env)
        if not args.skip_packages:
            install_packages(package_paths)
        logger.info(f"Venv {venv_name} updated successfully!")


if __name__ == "__main__":
    main()
