from __future__ import annotations

import enum

from maya import cmds

from ..abstract.app import AFnApp


class FileExtensions(enum.IntEnum):
    """
    Overload of IntEnum that contains the file extensions for Maya.
    """

    mb = 0
    ma = 1


class FnApp(AFnApp):
    """
    Overloads `AFnApp` exposing functions to handle application related behaviours
    for Maya application.
    """

    def extensions(self) -> tuple[FileExtensions, ...]:
        """
        Returns a list of application file extensions.

        :return: application file extensions.
        """

        return FileExtensions.ma, FileExtensions.mb

    def version(self) -> int | float:
        """
        Returns the version of the application.

        :return: application version.
        """

        return int(cmds.about(version=True))

    def version_name(self) -> str:
        """
        Returns the version name of the application.

        :return: application version name.
        """

p
    def is_batch(self) -> bool:
        """
        Returns whether the application is running in batch mode.

        :return: True if application is running in batch mode; False otherwise.
        """

        return cmds.about(batch=True)
