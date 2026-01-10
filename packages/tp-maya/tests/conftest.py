"""Pytest configuration and fixtures for tp-maya tests.

This module provides fixtures for both unit tests (no Maya required) and
integration tests (require Maya session via mayapy).

To run integration tests, use mayapy as the Python interpreter (PowerShell):
    & "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe" -m pytest tests/ -m integration

To run unit tests only (no Maya required):
    pytest tests/ -m "not integration"
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from typing import Generator


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""

    config.addinivalue_line(
        "markers",
        "integration: marks tests as requiring Maya (run with mayapy)",
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as pure unit tests (no Maya required)"
    )


# =============================================================================
# Maya Session Detection and Initialization
# =============================================================================


def _is_maya_available() -> bool:
    """Check if Maya modules are available for import.

    Returns:
        True if running inside Maya or mayapy, False otherwise.
    """

    try:
        import maya.cmds  # noqa: F401

        return True
    except ImportError:
        return False


def _is_maya_initialized() -> bool:
    """Check if Maya standalone has been initialized.

    Returns:
        True if Maya is initialized and ready to use.
    """

    try:
        import maya.cmds as cmds

        # Try a simple command to verify Maya is actually initialized
        cmds.about(version=True)
        return True
    except (ImportError, RuntimeError):
        return False


@pytest.fixture(scope="session")
def maya_session() -> Generator[None, None, None]:
    """Session-scoped fixture that initializes Maya standalone.

    This fixture should be used for integration tests that require
    a live Maya session. It initializes Maya standalone at the start
    of the test session and uninitializes it at the end.

    Yields:
        None - Maya is initialized and ready to use.

    Raises:
        pytest.skip: If Maya is not available.
    """

    if not _is_maya_available():
        pytest.skip(
            "Maya is not available - run with mayapy for integration tests"
        )

    if not _is_maya_initialized():
        import maya.standalone

        maya.standalone.initialize(name="python")

    yield

    # Note: We don't uninitialize maya.standalone here because it can cause
    # issues with subsequent test runs in the same process


@pytest.fixture
def new_scene(maya_session: None) -> Generator[None, None, None]:
    """Fixture that creates a fresh Maya scene for each test.

    This fixture depends on maya_session and creates a new empty scene
    before each test, ensuring test isolation.

    Args:
        maya_session: The maya_session fixture (dependency injection).

    Yields:
        None - A fresh scene is ready.
    """

    import maya.cmds as cmds

    cmds.file(new=True, force=True)
    yield
    cmds.file(new=True, force=True)


@pytest.fixture
def meta_registry_clean() -> Generator[None, None, None]:
    """Fixture that cleans the meta registry before and after tests.

    This ensures that custom meta classes registered during tests don't
    affect other tests.

    Yields:
        None - Registry is clean and ready.
    """

    from tp.libs.maya.meta.base import MetaRegistry

    # Store original registry state
    original_types = dict(MetaRegistry._CACHE)

    yield

    # Restore original registry state
    MetaRegistry._CACHE = original_types


@pytest.fixture
def property_registry_clean() -> Generator[None, None, None]:
    """Fixture that cleans the property registry before and after tests.

    This ensures that custom property classes registered during tests don't
    affect other tests.

    Yields:
        None - Registry is clean and ready.
    """

    from tp.libs.maya.meta.properties import PropertyRegistry

    # Store original registry state
    original_types = dict(PropertyRegistry._CACHE)
    original_hidden = dict(PropertyRegistry._HIDDEN)

    yield

    # Restore original registry state
    PropertyRegistry._CACHE = original_types
    PropertyRegistry._HIDDEN = original_hidden


# =============================================================================
# Mock Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_maya_cmds() -> MagicMock:
    """Fixture that provides a mock maya.cmds module.

    Use this for unit tests that need to verify calls to maya.cmds
    without actually running Maya.

    Returns:
        MagicMock configured to act like maya.cmds.
    """

    mock_cmds = MagicMock()

    # Configure common return values
    mock_cmds.objExists.return_value = True
    mock_cmds.nodeType.return_value = "network"
    mock_cmds.ls.return_value = []

    return mock_cmds


@pytest.fixture
def mock_maya_environment(
    mock_maya_cmds: MagicMock,
) -> Generator[MagicMock, None, None]:
    """Fixture that patches Maya modules for unit testing.

    This allows running tests that import Maya modules without
    actually having Maya available.

    Args:
        mock_maya_cmds: Mock cmds module fixture.

    Yields:
        The mock cmds module.
    """

    # Create mock modules
    mock_maya = MagicMock()
    mock_maya.cmds = mock_maya_cmds
    mock_maya.OpenMaya = MagicMock()
    mock_maya.OpenMayaAnim = MagicMock()

    # Patch sys.modules
    original_modules = {}
    modules_to_mock = [
        "maya",
        "maya.cmds",
        "maya.OpenMaya",
        "maya.OpenMayaAnim",
        "maya.api",
        "maya.api.OpenMaya",
        "maya.api.OpenMayaAnim",
    ]

    for mod_name in modules_to_mock:
        original_modules[mod_name] = sys.modules.get(mod_name)
        if mod_name == "maya":
            sys.modules[mod_name] = mock_maya
        elif mod_name == "maya.cmds":
            sys.modules[mod_name] = mock_maya_cmds
        else:
            sys.modules[mod_name] = MagicMock()

    yield mock_maya_cmds

    # Restore original modules
    for mod_name, original in original_modules.items():
        if original is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = original
