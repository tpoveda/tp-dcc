from __future__ import annotations

__version__ = "0.1.0"

import os
import site

from .core import log
from .core import constants
from .core.manager import PackagesManager
from .utils import dcc
from ..core.host import Host
from ..managers.tools import ToolsManager


def init() -> PackagesManager:
    """Initializes TP DCC Packages Manager.

    Returns:
        An instance of the TP DCC Packages Manager.

    Raises:
        ValueError: If the environment variable
            `TP_DCC_PIPELINE_ROOT_DIRECTORY` is not set.
    """

    root_path = os.getenv(constants.ROOT_DIRECTORY_ENV_VAR)
    root_path = os.path.abspath(root_path) if root_path else None
    if not root_path:
        raise ValueError(
            f"Environment variable {constants.ROOT_DIRECTORY_ENV_VAR} is not set."
        )

    site_packages_path = os.getenv(constants.SITE_PACKAGES_ENV_VAR)
    site_packages_path = (
        os.path.abspath(site_packages_path) if site_packages_path else None
    )
    if site_packages_path and os.path.exists(site_packages_path):
        site.addsitedir(site_packages_path)

    packages_manager = PackagesManager.current()
    if packages_manager is None:
        packages_manager = PackagesManager.from_path(root_path)
        setup_host(packages_manager)

        # Initialize tools manager.
        ToolsManager()

    return packages_manager


def setup_host(packages_manager: PackagesManager) -> Host:
    """Sets up the host application for the TP DCC pipeline.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager.

    Returns:
        An instance of the host application.

    Raises:
        NotImplementedError: If the host application is not implemented.
    """

    if dcc.is_standalone():
        from .hosts.standalone.host import StandaloneHost

        return Host.create(packages_manager, StandaloneHost, dcc.Standalone)

    if dcc.is_maya():
        from .hosts.maya.host import MayaHost

        return Host.create(packages_manager, MayaHost, dcc.Maya)
    else:
        raise NotImplementedError(f"Host not implemented for {dcc.current_dcc()}")


def shutdown():
    """Shuts down the TP DCC pipeline.

    This method should be called when the TP DCC pipeline is no longer needed.
    It will unload all packages and clean up any resources used by the
        pipeline.
    """

    packages_manager = PackagesManager.current()
    if packages_manager:
        packages_manager.shutdown()


# Setup TP DCC logger
log.setup_tp_dcc_logger()
