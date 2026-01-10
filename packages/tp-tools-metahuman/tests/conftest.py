"""Pytest configuration and fixtures for tp-tools-metahuman tests.

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
    # issues with subsequent test runs in the same session.


@pytest.fixture
def new_scene(maya_session) -> Generator[None, None, None]:
    """Fixture that creates a new Maya scene before each test.

    This fixture depends on maya_session and creates a fresh scene
    for each test, ensuring test isolation.

    Yields:
        None - A new empty scene is ready.
    """

    import maya.cmds as cmds

    cmds.file(new=True, force=True)

    yield

    # Clean up after test
    cmds.file(new=True, force=True)


# =============================================================================
# Mock Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_maya():
    """Provide mock Maya modules for unit testing without Maya.

    This fixture mocks the maya.cmds and maya.api modules for tests
    that need to test logic without actually running Maya.

    Returns:
        MagicMock: A mock object representing the maya module.
    """

    mock_maya_module = MagicMock()
    mock_maya_module.cmds = MagicMock()
    mock_maya_module.api = MagicMock()

    return mock_maya_module
