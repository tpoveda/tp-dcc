from __future__ import annotations

import typing

from tp.libs import dcc

if typing.TYPE_CHECKING:
    from .controllers.abstract import ARenamerController


class RenamerControllerFactory:
    """Factory class that returns the proper renamer controller based on the
    current DCC."""

    @staticmethod
    def controller() -> ARenamerController:
        """Return the proper renamer controller based on the current DCC.

        Returns:
            The renamer controller instance.
        """

        if dcc.is_maya():
            from .controllers.maya.controller import MayaRenamerController

            return MayaRenamerController()
        else:
            raise ValueError(f"Unsupported DCC: {dcc.current_dcc()}")
