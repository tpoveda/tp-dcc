from __future__ import annotations

from tp.preferences import manager


# noinspection PyUnresolvedReferences
def theme_interface() -> "ThemeInterface":
    """Return the interface to interact with the theme preferences.

    Returns:
        Theme interface instance.
    """

    return manager.current_instance().interface("theme")


# noinspection PyUnresolvedReferences
def general_interface() -> "GeneralInterface":
    """Return the interface to interact with the general preferences.

    Returns:
        General interface instance.
    """

    return manager.current_instance().interface("general")
