from __future__ import annotations

from tp.preferences import manager


# noinspection PyUnresolvedReferences
def nodegraph_interface() -> "ThemeInterface":
    """Return the interface to interact with the node graph library preferences.

    Returns:
        Nodegraph interface instance.
    """

    return manager.current_instance().interface("nodegraph")
