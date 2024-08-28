from __future__ import annotations

from abc import abstractmethod

from .base import AFnBase


class AFnApp(AFnBase):
    """
    Overloads `AFnBase` exposing functions to handle application related behaviours.
    """

    @abstractmethod
    def version(self) -> int | float:
        """
        Returns the version of the application.

        :return: application version.
        """

        pass

    @abstractmethod
    def version_name(self) -> str:
        """
        Returns the version name of the application.

        :return: application version name.
        """

        pass

    @abstractmethod
    def is_batch(self) -> bool:
        """
        Returns whether the application is running in batch mode.

        :return: True if application is running in batch mode; False otherwise.
        """

        pass
