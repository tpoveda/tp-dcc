from __future__ import annotations

from .core import Node, InputPort, OutputPort

__all__ = ["Node", "InputPort", "OutputPort", "startup", "shutdown"]


def startup():
    """Startup function to initialize the node graph library."""

    # Import config to initialize `ConfigManager`
    # This ensures that the default input actions are registered.
    from tp.libs.nodegraph.core import config  # noqa: F401

    # from tp.libs.nodegraph.core import registry
    from tp.libs.nodegraph.core.package import manager as packages_manager

    # registry.discover_plugins("tp.libs.nodegraph.nodes", lazy_load=False)
    packages_manager.initialize()


def shutdown():
    """Shutdown function to clean up the node graph library."""

    # Currently, no specific shutdown actions are required.
    pass
