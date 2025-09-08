from __future__ import annotations

import typing

from tp import dcc

if typing.TYPE_CHECKING:
    from .controllers.abstract import AMatchBakeController


class MatchBakeControllerFactory:
    """Factory class that returns the proper renamer controller based on the
    current DCC.
    """

    @staticmethod
    def controller() -> AMatchBakeController:
        """Return the proper renamer controller based on the current DCC.

        Raises:
            ValueError: If the current DCC is not supported.

        Returns:
            The renamer controller instance.
        """

        if dcc.is_maya():
            from .controllers.maya.controller import MayaMatchBakeController

            return MayaMatchBakeController()
        else:
            raise ValueError(f"Unsupported DCC: {dcc.current_dcc()}")
