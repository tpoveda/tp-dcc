from __future__ import annotations


def startup():
    """Startup function to initialize the node graph library."""

    # Import config to initialize `ConfigManager`
    # This ensures that the default input actions are registered.
    from tp.libs.nodegraph.core import config  # noqa: F401


def shutdown():
    """Shutdown function to clean up the node graph library."""

    # Currently, no specific shutdown actions are required.
    pass
