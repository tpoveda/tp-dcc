"""Pytest configuration and shared fixtures for templating library tests."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from typing import Generator

import pytest

# Add the src directory to the path if needed.
src_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tp.libs.templating.naming import config

# Try to import optional modules - some tests may be skipped if unavailable
try:
    from tp.libs.templating.naming import api, convention, preset

    HAS_FULL_DEPS = True
except ImportError:
    HAS_FULL_DEPS = False
    convention = None
    preset = None
    api = None


# Path to the test data directory.
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def requires_full_deps(func):
    """Decorator to skip tests that require full dependencies."""
    return pytest.mark.skipif(
        not HAS_FULL_DEPS,
        reason="Requires tp.libs.yaml and other dependencies",
    )(func)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Creates a temporary directory for test files.

    Yields:
        Path to the temporary directory.
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def reset_global_config() -> Generator[None, None, None]:
    """Resets the global configuration before and after each test.

    This ensures tests don't interfere with each other through global state.
    """
    config.reset_configuration()
    if HAS_FULL_DEPS and api is not None:
        api.reset_preset_manager()
    yield
    config.reset_configuration()
    if HAS_FULL_DEPS and api is not None:
        api.reset_preset_manager()


@pytest.fixture
def clean_config(reset_global_config) -> config.NamingConfiguration:
    """Returns a fresh NamingConfiguration instance.

    Returns:
        Clean NamingConfiguration instance with no preset paths.
    """
    return config.NamingConfiguration()


@pytest.fixture
def config_with_builtin_path(
    reset_global_config,
) -> config.NamingConfiguration:
    """Returns a NamingConfiguration with the built-in presets path.

    Returns:
        NamingConfiguration with built-in presets path added.
    """
    cfg = config.NamingConfiguration()
    builtin_path = config.builtin_presets_path()
    cfg.add_preset_path(builtin_path)
    return cfg


@pytest.fixture
def base_naming_convention():
    """Returns a naming convention loaded from base.json test data.

    Returns:
        NamingConvention instance loaded from base.json.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    base_path = os.path.join(TEST_DATA_DIR, "base.json")
    return convention.NamingConvention.from_path(base_path)


@pytest.fixture
def parent_naming_convention():
    """Returns a naming convention loaded from parent.json test data.

    Returns:
        NamingConvention instance loaded from parent.json.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    parent_path = os.path.join(TEST_DATA_DIR, "parent.json")
    return convention.NamingConvention.from_path(parent_path)


@pytest.fixture
def naming_convention_with_parent(
    base_naming_convention, parent_naming_convention
):
    """Returns a naming convention with a parent set.

    Returns:
        NamingConvention with parent naming convention.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    base_naming_convention.parent = parent_naming_convention
    return base_naming_convention


@pytest.fixture
def empty_naming_convention():
    """Returns an empty naming convention.

    Returns:
        Empty NamingConvention instance.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    return convention.NamingConvention()


@pytest.fixture
def simple_naming_convention():
    """Returns a simple naming convention with basic tokens and rules.

    Returns:
        NamingConvention with description, side, and type tokens.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    nc = convention.NamingConvention(naming_data={"name": "simple"})
    nc.add_token("description")
    nc.add_token("side", left="L", right="R", middle="M", default="M")
    nc.add_token(
        "type", animation="anim", control="ctrl", joint="jnt", default="ctrl"
    )
    nc.add_rule(
        "default",
        "{description}_{side}_{type}",
        {"description": "test", "side": "left", "type": "joint"},
    )
    return nc


@pytest.fixture
def preset_manager_with_default(
    config_with_builtin_path,
):
    """Returns a preset manager with the default preset loaded.

    Returns:
        PresetsManager with default preset loaded.
    """
    if not HAS_FULL_DEPS:
        pytest.skip("Requires full dependencies")
    return preset.PresetsManager.from_configuration(config_with_builtin_path)


@pytest.fixture
def temp_preset_dir(temp_dir) -> str:
    """Creates a temporary directory with test preset files.

    Yields:
        Path to directory containing test preset files.
    """
    # Create a simple preset file
    preset_content = """name: test
namingConventions:
- name: test-global
  type: global
"""
    preset_file = os.path.join(temp_dir, "test.preset")
    with open(preset_file, "w") as f:
        f.write(preset_content)

    # Create a simple naming convention file
    convention_content = """name: test-global
description: Test global naming convention
rules:
  - name: test_rule
    creator: test
    description: Test rule
    expression: "{prefix}_{name}_{suffix}"
    exampleFields:
      prefix: TST
      name: Object
      suffix: "01"
tokens:
  - name: prefix
    description: Object prefix
  - name: name
    description: Object name
  - name: suffix
    description: Object suffix
"""
    convention_file = os.path.join(temp_dir, "test-global.yaml")
    with open(convention_file, "w") as f:
        f.write(convention_content)

    return temp_dir
