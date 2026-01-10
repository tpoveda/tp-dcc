"""Script to run Maya integration tests using mayapy.

This script initializes Maya standalone and runs pytest with the specified
arguments. It should be executed with mayapy (Maya's Python interpreter).

The script automatically:
- Sets up TP DCC pipeline environment variables
- Configures the maya2026 virtual environment site-packages
- Initializes the TP framework via bootstrap
- Initializes Maya standalone

Usage (PowerShell):
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py [pytest arguments]

Examples:
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py                           # Run all tests
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py -m integration            # Run integration tests
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py -m "not integration"      # Run unit tests only
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py -v                        # Verbose output
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" scripts/run_maya_tests.py --cov=tp.tools.metahuman  # With coverage
"""

from __future__ import annotations

import os
import site
import sys
from pathlib import Path


def setup_environment():
    """Configure TP DCC pipeline environment and initialize the framework.

    This function:
    - Sets up TP_DCC_PIPELINE_ROOT_DIRECTORY environment variable
    - Sets up TP_DCC_PIPELINE_SITE_PACKAGES environment variable
    - Configures log level for debugging
    - Adds site packages to sys.path
    - Initializes the TP framework via bootstrap

    Returns:
        bool: True if environment was set up successfully.
    """

    # Find the repository root (tp-dcc)
    script_path = Path(__file__).resolve()
    # scripts/run_maya_tests.py -> tp-tools-metahuman -> packages -> tp-dcc
    repo_root = script_path.parent.parent.parent.parent

    # Define paths
    site_packages = repo_root / "envs" / "maya2026" / "Lib" / "site-packages"

    if not site_packages.exists():
        print(f"WARNING: Virtual environment not found at {site_packages}")
        print("Make sure to create the maya2026 virtual environment first.")
        return False

    # Set up environment variables
    os.environ["TP_DCC_PIPELINE_ROOT_DIRECTORY"] = str(repo_root)
    os.environ["TP_DCC_PIPELINE_SITE_PACKAGES"] = str(site_packages)
    os.environ["TP_DCC_LOG_LEVEL"] = "DEBUG"

    print(f"TP_DCC_PIPELINE_ROOT_DIRECTORY: {repo_root}")
    print(f"TP_DCC_PIPELINE_SITE_PACKAGES: {site_packages}")
    print("TP_DCC_LOG_LEVEL: DEBUG")

    # Add site packages to sys.path
    site.addsitedir(str(site_packages))
    print(f"Added site directory: {site_packages}")

    return True


def initialize_tp_framework():
    """Initialize the TP framework via bootstrap.

    Returns:
        bool: True if framework was initialized successfully.
    """

    try:
        from tp import bootstrap

        bootstrap.init()
        print("TP framework initialized successfully.")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import TP bootstrap: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to initialize TP framework: {e}")
        return False


def initialize_maya():
    """Initialize Maya standalone for testing.

    Returns:
        bool: True if Maya was initialized successfully, False otherwise.
    """

    try:
        import maya.standalone

        maya.standalone.initialize(name="python")
        print("Maya standalone initialized successfully.")
        return True
    except ImportError:
        print("ERROR: Maya modules not found. Run this script with mayapy.")
        return False
    except RuntimeError as e:
        # Maya might already be initialized
        if "already initialized" in str(e).lower():
            print("Maya standalone already initialized.")
            return True
        print(f"ERROR: Failed to initialize Maya: {e}")
        return False


def run_tests():
    """Run pytest with command line arguments."""

    import pytest

    # Default arguments if none provided
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Always include the tests directory
    if not any(arg.startswith("tests") for arg in args):
        args.insert(0, "tests")

    print(f"Running pytest with arguments: {args}")
    return pytest.main(args)


def main():
    """Main entry point."""

    print("=" * 60)
    print("MetaHuman Integration Test Runner")
    print("=" * 60)

    # Setup environment first (before Maya init to have correct paths)
    if not setup_environment():
        print("ERROR: Failed to setup environment.")
        sys.exit(1)

    # Initialize Maya standalone
    if not initialize_maya():
        sys.exit(1)

    # Initialize TP framework (after Maya so DCC detection works)
    if not initialize_tp_framework():
        sys.exit(1)

    print("=" * 60)
    exit_code = run_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
