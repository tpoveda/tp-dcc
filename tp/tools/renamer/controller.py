from __future__ import annotations

import typing

from tp import dcc

if typing.TYPE_CHECKING:
    from .controllers.abstract import ARenamerController


class RenamerControllerFactory:
    """Factory class that returns the proper renamer controller based on the current DCC."""

    @staticmethod
    def controller() -> ARenamerController:
        """
        Returns the proper renamer controller based on the current DCC.

        :return: renamer hook instance.
        """

        if dcc.is_maya():
            from .controllers.maya.controller import MayaRenamerController

            return MayaRenamerController()
        else:
            raise ValueError(f"Unsupported DCC: {dcc.current_dcc()}")
