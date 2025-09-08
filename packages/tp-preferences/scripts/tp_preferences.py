from __future__ import annotations

import typing

from loguru import logger

if typing.TYPE_CHECKING:
    from tp.bootstrap.core.manager import PackagesManager


# noinspection PyUnusedLocal
def startup(packages_manager: PackagesManager):
    """Startup function for tp-preferences package.

    This function is called when the package is loaded. It can be used to
    initialize the package, load plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

    from tp.libs.python import helpers
    from tp.preferences import manager
    from tp.preferences.interfaces import preferences
    from tp.preferences import style

    manager.current_instance().copy_preferences_to_root("user", force=False)

    style.setup()

    theme_interface = preferences.theme_interface()
    user_preferences = theme_interface.settings()
    user_styles = user_preferences.get("settings", {})
    default = manager.current_instance().default_preference_settings(
        "tp-preferences", "prefs/global/stylesheet"
    )
    default_styles = default.get("settings", {})

    # Update user styles if default styles have changed.
    _, message_log = helpers.compare_dictionaries(default_styles, user_styles)
    if message_log:
        user_preferences.save(indent=True, sort=True)
        logger.info(message_log)


# noinspection PyUnusedLocal
def shutdown(packages_manager: PackagesManager):
    """Shutdown function for tp-preferences package.

    This function is called when the package is unloaded. It can be used to
    clean up resources, unload plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

    from tp.preferences import manager
    from tp.preferences import style

    # Teardown styles
    style.shutdown()

    # Save the current preference roots.
    root_config = packages_manager.preference_roots_path()
    root_paths = {
        root_name: str(root_object)
        for root_name, root_object in manager.current_instance().roots.items()
    }
    # with open(root_config, "w") as file:
    #     yaml.dump(root_paths, file, default_flow_style=False)
