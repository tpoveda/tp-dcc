from __future__ import annotations

import sys
import typing

from loguru import logger
from maya.api import OpenMaya

if typing.TYPE_CHECKING:
    from tp.bootstrap.core.manager import PackagesManager

# Logger ID for Maya.
_logger_handle_id: int | None = None


# noinspection PyUnusedLocal
def startup(packages_manager: PackagesManager):
    """Startup function for tp-maya package.

    This function is called when the package is loaded. It can be used to
    initialize the package, load plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

    # setup_logger()


# noinspection PyUnusedLocal
def shutdown(packages_manager: PackagesManager):
    """Shutdown function for tp-maya package.

    This function is called when the package is unloaded. It can be used to
    clean up resources, unload plugins, etc.

    Args:
        packages_manager: The TP DCC Python pipeline packages manager instance.
    """

#     remove_logger()
#
#
# def setup_logger():
#     """Set up custom handler for Maya logger."""
#
#     global _logger_handle_id
#
#     _logger_handle_id = logger.add(
#         MayaLoguruHandler(),
#         level="DEBUG",
#         enqueue=True,
#         colorize=True,
#         format="{time:YYYY-MM-DD HH:mm:ss} [{level}] ({name}.{function}:{line}) > {message}",
#     )
#
#
# def remove_logger():
#     """Remove the custom Maya logger handler."""
#
#     global _logger_handle_id
#
#     if _logger_handle_id is not None:
#         logger.remove(_logger_handle_id)
#         _logger_handle_id = None
#
#
# class MayaLoguruHandler:
#     """Custom Loguru sink for Maya.
#
#     This class is used to display log messages in the Maya script editor.
#     It overrides the `__call__` method to handle different log levels and
#     display the messages accordingly and with the correct color.
#     """
#
#     def __call__(self, message):
#         text = message.format()
#         level = message.record["level"].name
#
#         if level == "INFO":
#             OpenMaya.MGlobal.displayInfo(text)
#         elif level == "WARNING":
#             OpenMaya.MGlobal.displayWarning(text)
#         elif level in ("ERROR", "CRITICAL"):
#             OpenMaya.MGlobal.displayError(text)
#         else:
#             sys.__stdout__.write(f"{text}\n")
#             sys.__stdout__.flush()
