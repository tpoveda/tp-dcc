from __future__ import annotations

import unreal

from ..abstract.app import AFnApp

class FnApp(AFnApp):
    """
    Overloads `AFnApp` exposing functions to handle application related behaviours
    for Unreal application.
    """

    def is_batch(self) -> bool:
        """
        Returns whether the application is running in batch mode.

        :return: True if application is running in batch mode; False otherwise.
        """

        return unreal.is_editor()
