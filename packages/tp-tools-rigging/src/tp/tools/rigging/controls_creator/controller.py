from __future__ import annotations

from tp import dcc

if dcc.is_maya():
    from .controllers.maya import (
        MayaControlsCreatorController as ControlsCreatorController,
    )
else:
    from .controllers.abstract import ControlsCreatorController
