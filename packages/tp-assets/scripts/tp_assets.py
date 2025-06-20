from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from tp.bootstrap.core.manager import PackagesManager


# noinspection PyUnusedLocal
def startup(packages_manager: PackagesManager):
    """Startup function for tp-assets package.

    This function is called when the package is loaded. It can be used to
    initialize the package, load plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

    pass


# noinspection PyUnusedLocal
def shutdown(packages_manager: PackagesManager):
    """Shutdown function for tp-assets package.

    This function is called when the package is unloaded. It can be used to
    clean up resources, unload plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

    pass
