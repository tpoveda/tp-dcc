from __future__ import annotations

from ..abstract.app import AFnApp


class FnApp(AFnApp):
    """
    Overloads `AFnApp` exposing functions to handle application related behaviours for Standalone application.
    """

    def version(self) -> int | float:
        """
        Returns the version of the application.

        :return: application version.
        """

        return 0.0

    def version_name(self) -> str:
        """
        Returns the version name of the application.

        :return: application version name.
        """

        return "0.0"

    def is_batch(self) -> bool:
        """
        Returns whether the application is running in batch mode.

        :return: True if application is running in batch mode; False otherwise.
        """

        return False
