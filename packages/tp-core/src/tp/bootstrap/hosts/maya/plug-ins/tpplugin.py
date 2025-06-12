from __future__ import annotations

import os
import site
import logging

from maya.api import OpenMaya

logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
def maya_useNewAPI():
    """Maya calls this function to indicate that the plugin uses
    OpenMaya 2.0 API.
    """

    pass


def _inject_paths():
    """Internal function that"""


def initialize():
    """Initializes the TP DCC Pipeline for Autodesk Maya."""

    logger.info("Loading TP DCC Pipeline for Maya, please wait ...")

    root_path = os.getenv("TP_DCC_PIPELINE_ROOT_DIRECTORY")
    root_path = os.path.abspath(root_path) if root_path else None
    if not root_path:
        raise ValueError(
            "Environment variable 'TP_DCC_PIPELINE_ROOT_DIRECTORY' is not set."
        )

    # Inject the TP DCC Pipeline site packages path into the Python path.
    site_packages_path = os.getenv("TP_DCC_PIPELINE_SITE_PACKAGES")
    site_packages_path = (
        os.path.abspath(site_packages_path) if site_packages_path else None
    )
    if not site_packages_path:
        raise ValueError(
            "Environment variable 'TP_DCC_PIPELINE_SITE_PACKAGES' is not set."
        )
    site.addsitedir(os.environ["TP_DCC_PIPELINE_SITE_PACKAGES"])

    from tp.bootstrap.core import host
    from tp.bootstrap.core import manager
    from tp.bootstrap.hosts.maya import host as maya_host

    packages_manager = manager.PackagesManager.current()
    if packages_manager is None:
        packages_manager = manager.PackagesManager.from_path(root_path)
        host.Host.create(packages_manager, maya_host.MayaHost, "maya")


def initializePlugin(obj: OpenMaya.MObject):
    """Initializes the TP DCC plugin for Autodesk Maya.

    Args:
        obj: The object to initialize the plugin for.
    """

    mplugin = OpenMaya.MFnPlugin(obj, "Tomi Poveda", "1.0")

    try:
        initialize()
    except Exception:
        logger.error(
            "Unhandled Exception occurred during TP DCC Pipeline for Maya startup",
            exc_info=True,
        )
        OpenMaya.MGlobal.displayError(
            "Unknown TP DCC Pipeline for Maya startup failure"
        )


def uninitializePlugin(obj):
    mplugin = OpenMaya.MFnPlugin(obj)
    try:
        from tp.bootstrap.core import manager

        packages_manager = manager.PackagesManager.current()
        if packages_manager is not None:
            packages_manager.shutdown()
    except Exception:
        logger.error(
            "Unhandled Exception occurred during TP DCC Pipeline for Maya shutdown",
            exc_info=True,
        )
        OpenMaya.MGlobal.displayError(
            "Unknown TP DCC Pipeline for Maya shutdown failure"
        )
